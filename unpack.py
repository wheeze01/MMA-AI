"""
Author: Nuekaze
License: BSD 2-Clause "Simplified" License
"""

# 필요한 라이브러리 임포트
import struct  # 바이너리 데이터를 해석하기 위한 모듈
import sys     # 명령줄 인수 처리 및 시스템 종료를 위한 모듈
import chardet # 문자열 인코딩 감지에 사용되는 라이브러리

# 도움말 출력 함수 정의
def help():
    print('Usage: motion.py input.vmd [output.csv] [OPTIONS]\n')  # 사용법 출력
    print('\n'.join([
        'List of options',
        '    -m, --motion:   Process motion data.',    # 본(Motion) 데이터 처리
        '    -f, --face:     Process face data.',      # 얼굴(Face) 데이터 처리
        '    -c, --camera:   Process camera data.',    # 카메라(Camera) 데이터 처리
        '',
        '    -h, --help:     Show this help message.', # 도움말 표시 옵션
        '    -v, --verbose:  Show some more info.',    # 자세한 정보 표시 옵션
        '    -d, --debug:    Enable debugging.',       # 디버깅 모드 활성화
    ]))

"""
명령줄 인수 처리 및 옵션 설정
"""
# 기본 옵션 초기화
skip = 0        # 사용자 입력을 건너뛸지 여부
motion = 0      # 본(Motion) 데이터 처리 여부
face = 0        # 얼굴(Face) 데이터 처리 여부
camera = 0      # 카메라(Camera) 데이터 처리 여부

# 도움말 출력 요청 확인
if '-h' in sys.argv or '--help' in sys.argv:
    help()  # 도움말 출력
    exit()  # 프로그램 종료

# 본 데이터 처리 옵션 설정
if '-m' in sys.argv or '--motion' in sys.argv:
    skip = 1  # 사용자 입력 건너뛰기
    motion = 1  # 본 데이터 처리 활성화

# 얼굴 데이터 처리 옵션 설정
if '-f' in sys.argv or '--face' in sys.argv:
    skip = 1  # 사용자 입력 건너뛰기
    face = 1  # 얼굴 데이터 처리 활성화

# 카메라 데이터 처리 옵션 설정
if '-c' in sys.argv or '--camera' in sys.argv:
    skip = 1  # 사용자 입력 건너뛰기
    camera = 1  # 카메라 데이터 처리 활성화

# 입력 파일 확인
try:
    # 첫 번째 명령줄 인수가 파일 이름인지 확인
    if sys.argv[1][0] == '-':
        print('Input file is required. Exiting.')
        exit()  # 파일이 없으면 종료
except IndexError:
    help()  # 인수가 없으면 도움말 출력
    exit()

# 사용자에게 데이터를 처리할지 여부를 묻는 인터랙티브 입력
if not skip:  # 사용자 입력을 건너뛰지 않을 경우
    m = input('Include motion data? [y/N]: ')  # 본 데이터 포함 여부
    if m == 'y' or m == 'Y':
        motion = 1  # 본 데이터 처리 활성화
    f = input('Include face data? [y/N]: ')  # 얼굴 데이터 포함 여부
    if f == 'y' or f == 'Y':
        face = 1  # 얼굴 데이터 처리 활성화
    c = input('Include camera data? [y/N]: ')  # 카메라 데이터 포함 여부
    if c == 'y' or c == 'Y':
        camera = 1  # 카메라 데이터 처리 활성화

# 디버그 및 자세한 출력 플래그 설정
debug = 0  # 디버깅 모드 비활성화
verbose = 0  # 자세한 정보 출력 비활성화
if '-d' in sys.argv or '--debug' in sys.argv:
    print('Debugging.')  # 디버깅 모드 활성화 메시지 출력
    debug = 1  # 디버깅 모드 활성화
    from pprint import pprint  # 디버깅용 데이터 출력 함수 임포트

if '-v' in sys.argv or '--verbose' in sys.argv:
    verbose = 1  # 자세한 정보 출력 활성화

# 기본 파일 이름 설정
motion_file = 'input.vmd'  # 입력 파일 기본값
output_file = 'output.csv'  # 출력 파일 기본값

# 명령줄 인수를 통해 입력 및 출력 파일 이름 설정
try:
    if sys.argv[1] and sys.argv[1][0] != '-':  # 입력 파일 이름 확인
        motion_file = sys.argv[1]  # 입력 파일 이름 설정
except IndexError:
    pass  # 인수가 없으면 기본값 사용

"""
VMD 파일 로드 및 기본 정보 처리
"""
# VMD 파일 읽기
raw = None  # 파일 내용 저장 변수
try:
    with open(motion_file, 'rb') as f:  # 바이너리 모드로 파일 열기
        if debug or verbose:
            print('Using %s\nLoading VMD file...' % motion_file)  # 파일 읽기 메시지 출력
        raw = f.read()  # 파일 내용을 변수에 저장
except FileNotFoundError:
    print('%s was not found.' % motion_file)  # 파일이 없으면 오류 메시지 출력
    exit()  # 프로그램 종료

# VMD 파일 헤더(버전 정보) 읽기
version = raw[0:30].split(b'\x00')[0].decode('utf-8')  # 버전 문자열 디코딩
if debug or verbose:
    print('MMD version: %s' % version)  # 버전 정보 출력

# 모델 이름 처리
model_name_encoding = "utf-8"  # 기본 UTF-8 인코딩
bones_name_encoding = "utf-8"  # 기본 UTF-8 인코딩

# 모델 이름 인코딩 감지 및 디코딩
try:
    model_name_encoding = chardet.detect(raw[30:50])['encoding']  # 인코딩 감지
    model = raw[30:50].split(b'\x00')[0].decode(model_name_encoding)  # 모델 이름 디코딩
    if debug or verbose:
        print('MMD model: %s' % model)  # 모델 이름 출력
except UnicodeDecodeError:
    print('No model is present. This is probably camera data.\nWill try to process camera data only.')
    motion = 0  # 본 데이터 비활성화
    face = 0  # 얼굴 데이터 비활성화
    camera = 2  # 카메라 데이터만 처리
    model = raw[30:50].hex()  # 모델 이름을 헥스 문자열로 저장

# 본 데이터 키프레임 개수 읽기
k_frames = struct.unpack('I', raw[50:54])[0]  # 4바이트 정수로 키프레임 개수 읽기
k_data = raw[54:]  # 본 데이터 시작 위치 저장

"""
본 데이터 처리
"""
motion_keyframes = []  # 본 키프레임 데이터를 저장할 리스트
if debug or verbose:
    print('Motion frames: %i' % k_frames)  # 키프레임 개수 출력
if camera != 2:  # 카메라 데이터만 처리하지 않을 경우
    if motion:  # 본 데이터 처리 활성화 여부 확인
        failed = 0  # 처리 실패한 키프레임 개수
        if debug or verbose:
            print('Processing motion data. This may take a few seconds...')  # 처리 메시지 출력
        for i in range(k_frames):  # 각 키프레임 반복 처리
            if debug:
                print(k_data[0:73])  # 현재 키프레임의 바이너리 데이터 출력(디버깅용)

            # 본 이름 읽기
            bone = ''  # 본 이름 초기화
            try:
                bone = k_data[0:15].split(b'\x00')[0].decode('utf-8')  # UTF-8로 디코딩
            except UnicodeDecodeError:
                try:
                    bones_name_encoding = "shift-jis"  # Shift-JIS로 변경
                    bone = k_data[0:15].split(b'\x00')[0].decode('shift-jis')  # Shift-JIS로 디코딩
                except UnicodeDecodeError:
                    try:
                        bones_name_encoding = chardet.detect(k_data[0:15].split(b'\x00')[0])['encoding']  # 인코딩 감지
                        bone = k_data[0:15].split(b'\x00')[0].decode(bones_name_encoding)  # 감지된 인코딩으로 디코딩
                    except UnicodeDecodeError:
                        failed += 1  # 실패한 키프레임 개수 증가
                    except TypeError:
                        failed += 1

            if bone:  # 본 이름이 유효할 경우
                # 키프레임 데이터 읽기
                frame = struct.unpack('I', k_data[15:19])[0]  # 프레임 번호
                xc = struct.unpack('f', k_data[19:23])[0]  # x 위치
                yc = struct.unpack('f', k_data[23:27])[0]  # y 위치
                zc = struct.unpack('f', k_data[27:31])[0]  # z 위치
                xr = struct.unpack('f', k_data[31:35])[0]  # x 회전
                yr = struct.unpack('f', k_data[35:39])[0]  # y 회전
                zr = struct.unpack('f', k_data[39:43])[0]  # z 회전

                # 보간 데이터 읽기
                i_data = k_data[43:111].hex()  # 68바이트 보간 데이터

                # 키프레임 데이터를 리스트에 추가
                motion_keyframes.append((frame, bone, xc, yc, zc, xr, yr, zr, i_data))
                k_data = k_data[111:]  # 다음 키프레임 데이터로 이동

        # 키프레임 정렬
        motion_keyframes.sort()
        if failed:
            print("Failed to decode %i bone frames." % failed)  # 실패 메시지 출력

    else:
        k_data = k_data[111*k_frames:]  # 본 데이터를 스킵

    if motion and debug:
        pprint(motion_keyframes)  # 본 데이터 출력 (디버깅용)

"""
얼굴 데이터 처리
"""
face_keyframes = []  # 얼굴 데이터의 키프레임을 저장할 리스트
k_frames = struct.unpack('I', k_data[0:4])[0]  # 키프레임 개수를 4바이트 정수로 읽음
k_data = k_data[4:]  # 키프레임 데이터 시작 위치를 업데이트
if debug or verbose:
    print('Face frames: %i' % k_frames)  # 키프레임 개수 출력 (디버깅/자세한 출력)

if camera != 2:  # 카메라 데이터만 처리하지 않을 경우
    if face:  # 얼굴 데이터 처리 활성화 여부 확인
        failed = 0  # 처리 실패한 키프레임 개수
        if debug or verbose:
            print('Processing face data. This may take a few seconds...')  # 처리 시작 메시지 출력
        for i in range(k_frames):  # 키프레임 개수만큼 반복
            if debug:
                print(k_data[0:73])  # 현재 키프레임의 바이너리 데이터 출력 (디버깅용)

            # 얼굴 데이터 이름 (Blendshape) 읽기
            try:
                blendshape = k_data[0:15].split(b'\x00')[0].decode('utf-8')  # UTF-8로 디코딩
            except UnicodeDecodeError:
                try:
                    blendshape = k_data[0:15].split(b'\x00')[0].decode('Shift_JIS')  # Shift-JIS로 디코딩
                except UnicodeDecodeError:
                    failed += 1  # 디코딩 실패 시 실패 개수 증가

            # 키프레임 데이터 읽기
            frame = struct.unpack('I', k_data[15:19])[0]  # 프레임 번호
            value = struct.unpack('f', k_data[19:23])[0]  # Blendshape 가중치

            # 키프레임 데이터를 리스트에 추가
            face_keyframes.append((frame, blendshape, value))
            k_data = k_data[23:]  # 다음 키프레임 데이터로 이동

        # 키프레임 정렬
        face_keyframes.sort()  # 프레임 번호를 기준으로 정렬
        if failed:
            print("Failed to decode %i blendshape frames." % failed)  # 실패 메시지 출력

    else:
        k_data = k_data[23*k_frames:]  # 얼굴 데이터를 스킵

    if face and debug:
        pprint(face_keyframes)  # 얼굴 데이터 출력 (디버깅용)

"""
카메라 데이터 처리
"""
camera_keyframes = []  # 카메라 데이터의 키프레임을 저장할 리스트
k_frames = struct.unpack('i', k_data[0:4])[0]  # 키프레임 개수를 4바이트 정수로 읽음
k_data = k_data[4:]  # 키프레임 데이터 시작 위치를 업데이트
if debug or verbose:
    print('Camera frames: %i' % k_frames)  # 키프레임 개수 출력 (디버깅/자세한 출력)

if camera:  # 카메라 데이터 처리 활성화 여부 확인
    if debug or verbose:
        print('Processing camera data. This may take a few seconds...')  # 처리 시작 메시지 출력
    for i in range(k_frames):  # 키프레임 개수만큼 반복
        if debug:
            print(k_data[0:61])  # 현재 키프레임의 바이너리 데이터 출력 (디버깅용)

        # 키프레임 데이터 읽기
        frame = struct.unpack('I', k_data[0:4])[0]  # 프레임 번호
        length = struct.unpack('f', k_data[4:8])[0]  # 카메라 거리 (Focal Length)
        xc = struct.unpack('f', k_data[8:12])[0]  # x 위치
        yc = struct.unpack('f', k_data[12:16])[0]  # y 위치
        zc = struct.unpack('f', k_data[16:20])[0]  # z 위치
        xr = struct.unpack('f', k_data[20:24])[0]  # x 회전
        yr = struct.unpack('f', k_data[24:28])[0]  # y 회전
        zr = struct.unpack('f', k_data[28:32])[0]  # z 회전
        i_data = k_data[32:56].hex()  # 보간 데이터
        fov = struct.unpack('I', k_data[56:60])[0]  # Field of View (FOV)
        perspective = k_data[60]  # 카메라 원근감 (1: 활성화, 0: 비활성화)

        # 키프레임 데이터를 리스트에 추가
        camera_keyframes.append((frame, length, xc, yc, zc, xr, yr, zr, i_data, fov, perspective))
        k_data = k_data[61:]  # 다음 키프레임 데이터로 이동

    if camera and debug:
        pprint(camera_keyframes)  # 카메라 데이터 출력 (디버깅용)

    # 키프레임 정렬
    camera_keyframes.sort()  # 프레임 번호를 기준으로 정렬

"""
결과 저장
"""
# 명령줄 인수를 통해 출력 파일 이름 설정
try:
    if sys.argv[2] and sys.argv[2][0] != '-':  # 출력 파일 이름 확인
        output_file = sys.argv[2]  # 출력 파일 이름 설정
except IndexError:
    pass  # 인수가 없으면 기본값 사용

# 데이터를 CSV 파일로 저장
with open(output_file, 'w') as f:
    if debug or verbose:
        print('Writing data to %s.' % output_file)  # 파일 저장 메시지 출력
    # 메타데이터 추가 (CSV에 주석 형식으로 작성)
    f.write('#%s;%s;%i;%i;%i;%s;%s\n' % (
        version,  # MMD 버전
        model,  # 모델 이름
        len(motion_keyframes),  # 본 데이터 키프레임 개수
        len(face_keyframes),  # 얼굴 데이터 키프레임 개수
        len(camera_keyframes),  # 카메라 데이터 키프레임 개수
        model_name_encoding,  # 모델 이름 인코딩
        bones_name_encoding  # 본 이름 인코딩
    ))

    # 본 데이터 저장
    if motion:
        f.write('\n'.join('%i;%s;%f;%f;%f;%f;%f;%f;%s' % x for x in motion_keyframes))
        f.write('\n')

    # 얼굴 데이터 저장
    if face:
        f.write('\n'.join('%i;%s;%f' % x for x in face_keyframes))
        f.write('\n')

    # 카메라 데이터 저장
    if camera:
        f.write('\n'.join('%i;%f;%f;%f;%f;%f;%f;%f;%s;%i;%i' % x for x in camera_keyframes))
        f.write('\n')

if debug or verbose:
    print('Done. Exiting.')  # 완료 메시지 출력
