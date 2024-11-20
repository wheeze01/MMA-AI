import numpy as np

# 저장된 텐서 파일 로드
tensor = np.load('Red Rose_motion.npy')  # 저장된 .npy 파일 경로
print("Tensor Shape:", tensor.shape)  # 텐서의 형태 확인
print("Tensor Data (Sample):", tensor[:5, :3, :])  # 일부 데이터 샘플 확인 (5 프레임, 3 본, 모든 특징)