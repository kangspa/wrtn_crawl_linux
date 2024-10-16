from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

import os
import pymysql
from time import sleep, time

from io import BytesIO
import base64
from PIL import Image

from multiprocessing import Pool, Manager
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

# mysql 연결
conn = pymysql.connect(
    host="localhost",
    port=3306,
    user="root",
    password="root",
    charset='utf8mb4'
)
cursor = conn.cursor()
# wrtn_char 데이터베이스 생성 / 이미 있다면 넘김
try:
    cursor.execute("CREATE DATABASE wrtn_char")
    conn.commit()
    print("Create DB Success")
except:
    print("Already exist DB(wrtn_char)")
# wrtn_char 데이터베이스 연결
cursor.execute("USE wrtn_char")

# 캐릭터 카테고리 테이블 생성 쿼리
create_cat = ''' CREATE TABLE `char_cat` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
	`name` VARCHAR(50) NOT NULL,
    `writer` VARCHAR(50) NOT NULL,
	`category` VARCHAR(20) NOT NULL
) CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;'''
# 캐릭터 정보 테이블 생성 쿼리
create_info = '''CREATE TABLE `char_info` (
    `id` INT,
	`name` VARCHAR(50) NOT NULL,
	`comment` TEXT NOT NULL,
	`first_dial` TEXT NOT NULL,
	`writer` VARCHAR(50) NOT NULL,
	`img` LONGBLOB NOT NULL,
	`ext` VARCHAR(5) NOT NULL,
	CONSTRAINT `fk_id` FOREIGN KEY (`id`) REFERENCES `char_cat` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;'''
# char_cat 테이블 생성 / 이미 있다면 넘김
try:
    cursor.execute(create_cat)
    conn.commit()
    print("Create Table Success(char_cat)")
except pymysql.MySQLError as e:
    print(f"Error {e.args[0]}: {e.args[1]}")
# char_info 테이블 생성 / 이미 있다면 넘김
try:
    cursor.execute(create_info)
    conn.commit()
    print("Create Table Success(char_info)")
except pymysql.MySQLError as e:
    print(f"Error {e.args[0]}: {e.args[1]}")
# mysql 연결 종료
conn.close()

# 크롤링 함수 작성 / 카테고리 번호를 입력받아서 해당 번호로 크롤링
def wrtnCharacterCrawl(cat_num):
    # mysql 연결
    conn = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="root",
        database="wrtn_char",
        charset='utf8mb4'
    )
    cursor = conn.cursor()
            
    options = webdriver.ChromeOptions()
    # 창 안 띄우는 옵션 등
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    # 크롬 다운로드 경로를 현재 경로의 img 폴더 안으로 변경
    prefs = {"download.default_directory": os.path.join(os.getcwd(),"img")}
    options.add_experimental_option("prefs", prefs)
    # 옵션 적용해서 브라우저 실행
    driver = webdriver.Chrome(options=options)
    
    # '캐릭터 둘러보기' 페이지 이동
    driver.get("https://wrtn.ai/character")
    
    # 해당 카테고리를 선택
    cat = driver.find_element(By.CSS_SELECTOR, f'.css-1fzkvcn > *:nth-child({cat_num})')
    # db에 저장할 카테고리명 추출
    db_category = cat.text
    # 현재 탐색 중인 카테고리명 출력
    print(f"Now Crawling:{db_category}")
    # 해당 카테고리 클릭
    cat.click()
    # 카테고리 클릭 후 로딩을 기다린다.
    sleep(5)
    
    # 0부터 캐릭터가 없어질 때까지 크롤링할 예정이므로 while문, flag 변수는 해당 카테고리를 마지막까지 훑었는지 확인
    dataIdx, flag = 0, 0
    while True:
        try:
            print(f"Now crawl : {dataIdx}")
            # 특정 캐릭터 선택
            each_selector = f'.virtuoso-grid-item[data-index="{dataIdx}"]'
            # 해당 캐릭터 요소를 element에 저장
            element = driver.find_element(By.CSS_SELECTOR, each_selector)
            # 캐릭터 요소를 이상없이 불러오면 flag는 0으로 초기화
            flag = 0
            # 해당 요소를 text로 파싱한 후, 개행 문자 기준으로 나눠서 캐릭터명, 설명, 작성자를 저장
            db_name, db_comment, db_writer = element.text.split('\n')
            # 클릭해서 들어가는 요소와, 이미지 요소의 선택자를 별도 작성
            clk_selector = each_selector+'>div>div:first-child'
            img_selector = clk_selector+'>div:first-child>.character_avatar>img'
            # 이미지 요소의 url 선택
            img_url = driver.find_element(By.CSS_SELECTOR, img_selector).get_attribute('src')
            # 해당 url에서 이미지 파일명과 확장자를 별도로 저장
            img_name, db_ext = img_url.split('/')[-1].split('.')
            # 이미지 다운로드 (해당 이미지의 url로 접근 시 자동 다운)
            driver.get(img_url)
            # 다운로드 시간을 대기
            sleep(10)
            # 다운로드된 이미지 경로
            img_dir = os.path.join("./img", img_name+'.'+db_ext)
            # 이미지를 BLOB으로 저장 가능하도록 인코딩
            buffer = BytesIO()
            im = Image.open(img_dir)
            im.save(buffer, format=db_ext)
            db_img = base64.b64encode(buffer.getvalue())
            db_img = db_img.decode('UTF-8')
            # 실제 이미지 파일은 삭제
            os.remove(img_dir)
            # 선택했던 캐릭터의 모달 창 열람
            driver.find_element(By.CSS_SELECTOR, clk_selector).click()
            sleep(3) # 새로 로딩되니까 대기
            # 모달 창 내에서 '대화 나누기' 클릭
            driver.find_element(By.CSS_SELECTOR, "#web-modal>div>div>div>div:nth-child(4)>button").click()
            sleep(10) # 새로 로딩되니까 대기
            # 첫번째 대사를 텍스트로 파싱
            db_first_dial = driver.find_element(By.CSS_SELECTOR, '.message-bubble.css-1oinfq4').text
            # 페이지 뒤로 가기 및 잠시 대기
            driver.back()
            sleep(5)
            # 방금 찾은 캐릭터가 나올 때까지 스크롤 다운
            try:
                each_selector = f'.virtuoso-grid-item[data-index="{dataIdx}"]'
                element = driver.find_element(By.CSS_SELECTOR, each_selector)
            except NoSuchElementException:
                scrollable_div = driver.find_element(By.CSS_SELECTOR, "#character-home-scroll")
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                sleep(3)
            
            # 캐릭터 카테고리 테이블에 저장하기
            print(f"Inserting into char_cat: {db_name}, {db_writer}, {db_category}")
            try:
                query = "INSERT INTO char_cat (name, writer, category) VALUES (%s, %s, %s)"
                cursor.execute(query, (db_name, db_writer, db_category))
                conn.commit()
                print(f"SUCCESS:insert {db_name}, {db_writer} to char_cat")
            # 실패 시 에러 확인
            except pymysql.MySQLError as e:
                print(f"Fail to Insert {db_name}, {db_writer} to char_cat({db_category})")
                print(f"Error {e.args[0]}: {e.args[1]}")
            # char_cat 테이블에서 생성된 id 값 가져오기
            cursor.execute("SELECT id FROM char_cat WHERE name = %s AND writer = %s", (db_name, db_writer))
            db_id = cursor.fetchone()[0]
            # 캐릭터 정보 테이블에 저장하기
            print(f"Inserting into char_info: {db_id}, {db_name}, {db_comment}, {db_first_dial}, {db_writer}, {db_ext}")
            try:
                query = "INSERT INTO char_info (id, name, comment, first_dial, writer, img, ext) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(query, (db_id, db_name, db_comment, db_first_dial, db_writer, db_img, db_ext))
                conn.commit()
                print(f"SUCCESS:insert {db_name}, {db_writer} to char_info")
            # 실패 시 에러 확인
            except pymysql.MySQLError as e:
                print(f"Fail to Insert {db_name}, {db_writer} to char_info({db_category})")
                print(f"Error {e.args[0]}: {e.args[1]}")
            
            # 다음 캐릭터 크롤링을 위해 +1
            dataIdx += 1
        except NoSuchElementException:
            print("Now Scroll to down")
            # 만약 2번이나 스크롤해서 캐릭터 로딩이 안됐다면, 다음 카테고리를 탐색
            if flag==2: break
            # flag를 1번씩 더함으로써, 캐릭터 로딩이 몇번이나 안됐는지 확인한다.
            flag += 1
            # 스크롤 가능 오브젝트가 윈도우가 아니라, #character-home-scroll, 해당 오브젝트를 변수로 저장
            # 로드된 캐릭터들 전부 크롤링했다면, 스크롤을 더 내려서 캐릭터를 로드한다.
            scrollable_div = driver.find_element(By.CSS_SELECTOR, "#character-home-scroll")
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            sleep(3)
    # 크롬브라우저 종료
    driver.quit()
    # mysql 연결 종료
    conn.close()
    
# 멀티스레드 크롤링 함수
def thread_crawler(cat_num):
    with ThreadPoolExecutor(max_workers=24) as executor:
        executor.submit(wrtnCharacterCrawl, cat_num)

if __name__ == "__main__":
    # 카테고리별로 작업 분할을 위한 리스트 / 2~11까지 각 카테고리의 순서(로맨스~기타)
    cat_list = range(2, 12)
    
    start = time()
    # 멀티프로세스 실행
    with Pool(processes=8) as pool:
        pool.map(thread_crawler, cat_list)
    print("*"*100)
    print(time()-start) #3643.7741239070892