# 베이스 이미지 설정
FROM python:3.12.3

# 작업 디렉토리 설정
WORKDIR /app

# Poetry 설치
RUN pip install poetry

# 의존성 파일 복사
COPY pyproject.toml poetry.lock ./

# 의존성 설치
RUN poetry install

# Chrome 및 ChromeDriver 설치에 필요한 패키지 설치 및 업데이트
RUN apt-get update && apt-get install -y wget unzip curl

# Chrome 설치
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

RUN apt -y install ./google-chrome-stable_current_amd64.deb

# ChromeDriver 설치를 위한 sh 파일 복사
COPY install_chromedriver.sh ./

# 권한 부여 후 설치
RUN chmod +x install_chromedriver.sh

RUN bash -x ./install_chromedriver.sh

# 애플리케이션 소스 코드 복사
COPY . .

# 애플리케이션 실행
CMD ["poetry", "run", "python", "pipeline.py"]