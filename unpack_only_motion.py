import struct
import os  # 폴더 내 파일 목록 확인 및 경로 처리를 위한 모듈
import sys

# 도움말 출력 함수
def help():
    print('Usage: motion.py [OPTIONS]\n')
    print('\n'.join([
        'List of options',
        '    -d, --debug:    Enable debugging.',  # 디버깅 모드
        '    -v, --verbose:  Show some more info.',  # 자세한 정보 출력
    ]))

"""
옵션 설정
"""
debug = 0
verbose = 0
if '-d' in sys.argv or '--debug' in sys.argv:
    print('Debugging enabled.')
    debug = 1  # 디버깅 모드 활성화
    from pprint import pprint  # 디버깅용 출력

if '-v' in sys.argv or '--verbose' in sys.argv:
    verbose = 1  # 자세한 정보 출력 활성화

"""
폴더 내 VMD 파일 검색
"""
# 현재 폴더의 모든 .vmd 파일 가져오기
input_folder = os.getcwd()  # 현재 작업 디렉터리
vmd_files = [f for f in os.listdir(input_folder) if f.endswith('.vmd')]  # .vmd 파일 필터링

if not vmd_files:  # .vmd 파일이 없는 경우
    print("No .vmd files found in the folder.")
    exit()

print(f"Found {len(vmd_files)} .vmd files: {vmd_files}")

"""
VMD 파일 처리 함수
"""
def process_motion_data(motion_file, output_file):
    try:
        # VMD 파일 로드
        with open(motion_file, 'rb') as f:
            if debug or verbose:
                print(f'Processing {motion_file}')
            raw = f.read()  # 파일 데이터 읽기
    except FileNotFoundError:
        print(f'{motion_file} not found.')
        return

    # 헤더 및 기본 정보
    version = raw[0:30].split(b'\x00')[0].decode('utf-8')  # 버전 정보 읽기
    if debug or verbose:
        print(f'MMD version: {version}')

    # 본 데이터 키프레임 개수
    k_frames = struct.unpack('I', raw[50:54])[0]  # 키프레임 개수
    k_data = raw[54:]  # 본 데이터 시작 위치

    motion_keyframes = []  # 본 키프레임 데이터를 저장할 리스트

    if debug or verbose:
        print(f'Motion frames: {k_frames}')  # 키프레임 개수 출력

    # 본 데이터 처리
    failed = 0  # 처리 실패한 키프레임 개수
    for i in range(k_frames):  # 각 키프레임 반복 처리
        try:
            # 본 이름 읽기
            bone = k_data[0:15].split(b'\x00')[0].decode('utf-8')
        except UnicodeDecodeError:
            try:
                bone = k_data[0:15].split(b'\x00')[0].decode('shift-jis')  # Shift-JIS로 디코딩
            except UnicodeDecodeError:
                failed += 1  # 실패한 경우 개수 증가
                k_data = k_data[111:]  # 실패 시 다음 키프레임으로 이동
                continue  # 현재 키프레임 스킵

        # 프레임 번호 및 위치/회전 정보 읽기
        frame = struct.unpack('I', k_data[15:19])[0]
        xc = struct.unpack('f', k_data[19:23])[0]
        yc = struct.unpack('f', k_data[23:27])[0]
        zc = struct.unpack('f', k_data[27:31])[0]
        xr = struct.unpack('f', k_data[31:35])[0]
        yr = struct.unpack('f', k_data[35:39])[0]
        zr = struct.unpack('f', k_data[39:43])[0]

        # 보간 데이터는 무시하고 필요한 데이터만 저장
        motion_keyframes.append((frame, bone, xc, yc, zc, xr, yr, zr))

        # 다음 키프레임으로 이동
        k_data = k_data[111:]

    if debug or verbose:
        print(f"Processed {len(motion_keyframes)} motion keyframes, failed {failed}")

    # 데이터를 CSV로 저장
    with open(output_file, 'w', encoding='utf-8') as f:  # UTF-8 인코딩 추가
        if debug or verbose:
            print(f'Writing motion data to {output_file}')
        # CSV 헤더 추가
        f.write('Frame;Bone;X;Y;Z;RotX;RotY;RotZ\n')
        # 데이터 추가
        f.write('\n'.join('%i;%s;%f;%f;%f;%f;%f;%f' % x for x in motion_keyframes))

"""
폴더 내 모든 VMD 파일 처리
"""
for vmd_file in vmd_files:
    # 입력 파일 이름에서 출력 파일 이름 생성
    output_file = os.path.splitext(vmd_file)[0] + '_motion.csv'
    process_motion_data(vmd_file, output_file)  # 모션 데이터 처리
    print(f"Motion data from {vmd_file} saved to {output_file}")

print("All files processed.")
