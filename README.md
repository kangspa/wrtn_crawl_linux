# 파이프라인을 실행하기 위한 스크립트

모든 실습은 Window 환경에서 진행되었고, 이후 WSL 환경에서 도커 이미지 구축 및 테스트가 진행되었습니다.

- docker-install.sh 파일을 통해 도커 설치
```
sudo sh ./docker-install.sh
```
- 도커 엔진을 실행
```
sudo /etc/init.d/docker start
```
```
systemctl enable docker
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

1. '캐릭터 둘러보기' 에서 각 카테고리별로 멀티스레드 작업을 진행
2. 각 카테고리별 명칭을 '캐릭터 카테고리' 로 저장
3. .virtuoso-grid-item[data-index="{}"] 요소를 텍스트로 파싱한 후, '캐릭터명', '캐릭터 설명', '캐릭터 작성자' 확인
4. .virtuoso-grid-item[data-index="{}"] 의 img 태그를 확인하여 '캐릭터 사진 원본의 blob image file' url 확인
5. .virtuoso-grid-item[data-index="{}"] 요소를 클릭하여 모달 창 열람
6. 모달 창에서 '대화하기' 버튼 클릭 후, .message-bubble.css-1oinfq4 요소에서 '캐릭터의 첫 메시지' 확인
7. 뒤로가기를 한 후, 현재까지 탐색하던 캐릭터 정보가 나올 때까지 스크롤
8. DB에 현재 탐색한 캐릭터 정보들을 저장, data-index 값을 +1 해서 다음 캐릭터를 크롤링한다.
9. 만약 해당 data-index의 캐릭터가 없다면, 스크롤을 아래로 내리고 로딩을 기다린다. (스크롤 요소는 window가 아니라 #character-home-scroll)
10. 로딩 후에도 캐릭터가 없다면, 해당 스레드는 종료
