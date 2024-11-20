import struct
import os  # 폴더 내 파일 목록 확인 및 경로 처리를 위한 모듈
import numpy as np  # 텐서 처리를 위한 라이브러리
import sys

debug = 0
verbose = 0

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
def process_motion_data_to_tensor(motion_file):
    try:
        # VMD 파일 로드
        with open(motion_file, 'rb') as f:
            if debug or verbose:
                print(f'Processing {motion_file}')
            raw = f.read()  # 파일 데이터 읽기
    except FileNotFoundError:
        print(f'{motion_file} not found.')
        return None

    # 헤더 및 기본 정보
    version = raw[0:30].split(b'\x00')[0].decode('utf-8')  # 버전 정보 읽기
    if debug or verbose:
        print(f'MMD version: {version}')

    # 본 데이터 키프레임 개수
    k_frames = struct.unpack('I', raw[50:54])[0]  # 키프레임 개수
    k_data = raw[54:]  # 본 데이터 시작 위치

    motion_keyframes = []  # 본 키프레임 데이터를 저장할 리스트
    bones = []  # 고유한 본 이름을 저장

    if debug or verbose:
        print(f'Motion frames: {k_frames}')  # 키프레임 개수 출력

    # 본 데이터 처리
    for i in range(k_frames):  # 각 키프레임 반복 처리
        try:
            # 본 이름 읽기
            bone = k_data[0:15].split(b'\x00')[0].decode('utf-8')
            if bone not in bones:
                bones.append(bone)  # 새로운 본 이름 추가
        except UnicodeDecodeError:
            bone = f"Unknown_Bone_{i}"  # 디코딩 실패 시 기본 이름
            if bone not in bones:
                bones.append(bone)

        # 프레임 번호 및 위치/회전 정보 읽기
        frame = struct.unpack('I', k_data[15:19])[0]
        xc = struct.unpack('f', k_data[19:23])[0]
        yc = struct.unpack('f', k_data[23:27])[0]
        zc = struct.unpack('f', k_data[27:31])[0]
        xr = struct.unpack('f', k_data[31:35])[0]
        yr = struct.unpack('f', k_data[35:39])[0]
        zr = struct.unpack('f', k_data[39:43])[0]

        # 데이터 추가
        motion_keyframes.append((frame, bone, xc, yc, zc, xr, yr, zr))

        # 다음 키프레임으로 이동
        k_data = k_data[111:]

    # 프레임 수 및 본 수 확인
    frames = sorted(set(kf[0] for kf in motion_keyframes))  # 고유한 프레임 번호
    num_frames = len(frames)
    num_bones = len(bones)

    # 텐서 초기화 (프레임 수 x 본 수 x 특징 수)
    tensor = np.zeros((num_frames, num_bones, 6))  # 6은 [X, Y, Z, RotX, RotY, RotZ]

    # 텐서에 데이터 채우기
    for frame, bone, xc, yc, zc, xr, yr, zr in motion_keyframes:
        frame_idx = frames.index(frame)  # 프레임 인덱스
        bone_idx = bones.index(bone)  # 본 인덱스
        tensor[frame_idx, bone_idx, :] = [xc, yc, zc, xr, yr, zr]  # 데이터 저장

    print(f"Processed Tensor Shape for {motion_file}: {tensor.shape}")
    return tensor

"""
폴더 내 모든 VMD 파일 처리 및 텐서 저장
"""
for vmd_file in vmd_files:
    # 텐서 처리
    tensor = process_motion_data_to_tensor(vmd_file)
    if tensor is not None:
        # 텐서 저장 (.npy 형식)
        output_file = os.path.splitext(vmd_file)[0] + '_motion.npy'
        np.save(output_file, tensor)
        print(f"Tensor data from {vmd_file} saved to {output_file}")

print("All files processed.")
