# 파이프라인을 실행하기 위한 스크립트

모든 실습은 Window 환경에서 진행되었고, 이후 WSL 환경에서 도커 이미지 구축 및 테스트가 진행되었습니다.   
Window 환경에서 10월16일(수) 'pipeline_multi_at_window.py' 를 통해 크롤링 및 최종 산출물을 만들고, 이후 WSL 환경에서 docker-compose.yml이 작동되도록 하였습니다.   
WSL 환경에서는 'pipeline_multi.py' 작동이 불안정한 듯 보여, 동작 확인을 위해 'pipeline.py'로 작동하도록 작성되어 있습니다.

## Docker 구동을 위한 WSL2 환경 구축

1. Window 환경에서 '[Ubuntu 22.04.2 LTS](https://apps.microsoft.com/store/detail/ubuntu-22042-lts/9PN20MSR04DW?hl=ko-kr&gl=ko)' 다운로드 및 설치
2. Powershell을 관리자모드로 실행 후, ```wsl -l -v```로 우분투 버전 확인
	- 만약 버전이 1이라면, ```wsl --set-default-version Ubuntu-22.04 2```로 버전을 바꿔주고, 확인해본다.
3. Powershell을 관리자모드로 실행해서 ```wsl -d Ubuntu-22.04```로 WSL Ubuntu 셀로 진입
	- 혹은 설치했던 Ubuntu 앱으로 진입
4. 아래 명령어를 통해 도커를 설치해준다.
```bash
$ curl -fsSL https://get.docker.com -o docker-install.sh
$ sudo sh ./docker-install.sh
```
5. ```sudo docker ps```를 입력하여 도커가 정상 작동 중인지 에러가 뜨는지 확인
	- 에러 발생 시, 상단 참고 링크 통해서 설정을 바꿔주고 리부트 한다. (테스트 당시 바로 정상 작동해서 패스)
6. ```sudo usermod -aG docker $USER```를 통해 docker 그룹에 사용자 추가
7. ```sudo chmod 666 /var/run/docker.sock```를 통해 권한 변경
8. ```sudo apt install docker-compose```를 통해 docker-compose 명령어 사용가능하도록 변경

- 참고 링크
	- [윈도우 WSL에서 Docker 설치하는 방법](https://www.lainyzine.com/ko/article/how-to-install-docker-on-wsl/#google_vignette)
 	- [도커 데스크톱 없이 구축하는 WSL2와 도커 개발 환경](https://netmarble.engineering/docker-on-wsl2-without-docker-desktop/)

## 도커 환경에 크롬 설치

1. Chrome의 경우, Dockerfile에 다운 및 설치가 바로 명시되어 있다.
2. ChromeDriver의 경우, `install_chromedriver.sh` 파일을 통해 설치를 진행한다.
	- 만약 해당 파일이 없을 경우, 아래와 같이 만들어서 Dockerfile과 동일 경로에 둔다.
```bash
#!/bin/bash

# Chrome 버전 확인
CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
echo "Detected Chrome version: $CHROME_VERSION"

# ChromeDriver 다운로드 URL
CHROMEDRIVER_URL="https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_VERSION}/linux64/chromedriver-linux64.zip"

# ChromeDriver 다운로드 및 설치
wget -O chromedriver_linux64.zip $CHROMEDRIVER_URL
unzip -o chromedriver_linux64.zip
mv -f chromedriver-linux64/chromedriver /usr/local/bin/chromedriver
chown root:root /usr/local/bin/chromedriver
chmod +x /usr/local/bin/chromedriver

# 정리
rm -rf chromedriver_linux64.zip chromedriver-linux64

echo "ChromeDriver $CHROME_VERSION has been installed successfully."
chromedriver --version
```

- 참고 링크
	- [WSL2에서 Selenium 사용하기](https://makepluscode.tistory.com/entry/WSL2에서-Selenium-사용하기)

## 도커 컨테이너 실행
```bash
docker-compose up --build
```

실행 후 에러 발생 시 아래와 같이 컨테이너 완전 종료 및 이미지 제거
```bash
$ docker-compose down
$ docker rmi -f mysql:8.0.39
```

---
# 데이터 스키마

- '캐릭터 카테고리' 는 캐릭터를 검색하는 데이터 기준으로 삼는다.
- '캐릭터 정보' 는 캐릭터 페이지에 진입했을 때 보이는 데이터를 기준으로 삼는다.
- 두 테이블에 id 컬럼을 만들어 연결해둔다.

```sql
CREATE TABLE `char_cat` (
	`id` INT AUTO_INCREMENT PRIMARY KEY,
	`name` VARCHAR(50) NOT NULL,
	`writer` VARCHAR(50) NOT NULL,
	`category` VARCHAR(20) NOT NULL
) CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
```

```sql
CREATE TABLE `char_info` (
	`id` INT,
	`name` VARCHAR(50) NOT NULL,
	`comment` TEXT NOT NULL,
	`first_dial` TEXT NOT NULL,
	`writer` VARCHAR(50) NOT NULL,
	`img` LONGBLOB NOT NULL,
	`ext` VARCHAR(5) NOT NULL,
	CONSTRAINT `fk_id` FOREIGN KEY (`id`) REFERENCES `char_cat` (`id`)
	ON DELETE CASCADE ON UPDATE CASCADE
) CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
```

---
# 크롤링 전략

1. '캐릭터 둘러보기' 에서 각 카테고리별로 멀티스레드&멀티프로세스 작업을 진행
2. 각 카테고리별 명칭을 '캐릭터 카테고리' 로 저장
3. .virtuoso-grid-item[data-index="{}"] 요소를 텍스트로 파싱한 후, '캐릭터명', '캐릭터 설명', '캐릭터 작성자' 확인
4. .virtuoso-grid-item[data-index="{}"] 의 img 태그를 확인하여 '캐릭터 사진 원본의 blob image file' url 확인
5. .virtuoso-grid-item[data-index="{}"] 요소를 클릭하여 모달 창 열람
6. 모달 창에서 '대화하기' 버튼 클릭 후, .message-bubble.css-1oinfq4 요소에서 '캐릭터의 첫 메시지' 확인
7. 뒤로가기를 한 후, 현재까지 탐색하던 캐릭터 정보가 나올 때까지 스크롤
8. DB에 현재 탐색한 캐릭터 정보들을 저장, data-index 값을 +1 해서 다음 캐릭터를 크롤링한다.
9. 만약 해당 data-index의 캐릭터가 없다면, 스크롤을 아래로 내리고 로딩을 기다린다. (스크롤 요소는 window가 아니라 #character-home-scroll)
10. 로딩 후에도 캐릭터가 없다면, 해당 프로세스는 종료
