# 베이스 이미지 설정
FROM python:3.12.3

# 작업 디렉토리 설정
WORKDIR ./

# Poetry 설치
RUN pip install poetry

# 의존성 파일 복사
COPY pyproject.toml poetry.lock ./

# 의존성 설치
RUN poetry install

# 애플리케이션 소스 코드 복사
COPY . .

# 애플리케이션 실행
CMD ["poetry", "run", "python", "pipeline_multi.py"]