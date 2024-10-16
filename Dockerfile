# 베이스 이미지 설정
FROM python:3.12.3

# MySQL 설치
RUN apt-get update && \
    apt-get install -y default-mysql-server && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# MySQL 데이터 디렉토리 생성
RUN mkdir -p /var/run/mysqld && \
    chown mysql:mysql /var/run/mysqld

# MySQL 초기 설정
COPY my.cnf /etc/mysql/my.cnf
RUN service mysql start && \
    mysql -u root -e "SET PASSWORD FOR 'root'@'localhost' = PASSWORD('root');"

# 작업 디렉토리 설정
WORKDIR /app

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