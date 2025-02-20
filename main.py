from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from time import sleep
from tqdm import tqdm
import base64
import ddddocr


chrome_options = Options()
driver = webdriver.Chrome(options=chrome_options)

driver.get("https://sep.ucas.ac.cn/")


def get_captcha():
    ele_captcha = driver.find_element(By.ID, "code")
    # get the captcha as a base64 string
    img_captcha_base64 = driver.execute_async_script(
        """
        var ele = arguments[0], callback = arguments[1];
        ele.addEventListener('load', function fn(){
        ele.removeEventListener('load', fn, false);
        var cnv = document.createElement('canvas');
        cnv.width = this.width; cnv.height = this.height;
        cnv.getContext('2d').drawImage(this, 0, 0);
        callback(cnv.toDataURL('image/jpeg').substring(22));
        }, false);
        ele.dispatchEvent(new Event('load'));
        """,
        ele_captcha,
    )

    with open("captcha.jpg", "wb") as f:
        f.write(base64.b64decode(img_captcha_base64))

    ocr = ddddocr.DdddOcr(show_ad=False)
    with open("captcha.jpg", "rb") as f:
        img_bytes = f.read()

    return ocr.classification(img_bytes)


def login_sep(LOGIN, PASSWORD):
    driver.set_page_load_timeout(20)
    driver.get("https://sep.ucas.ac.cn/")
    print("browser opened")
    # wait until sb1 shows up
    driver.find_element(By.ID, "userName1").send_keys(LOGIN)
    driver.find_element(By.ID, "pwd1").send_keys(PASSWORD)
    driver.find_element(By.ID, "certCode1").send_keys(get_captcha())
    driver.find_element(By.ID, "sb1").click()
    print("logged in")


def get_courses():
    driver.get("https://sep.ucas.ac.cn/portal/site/524/2412")
    sleep(10)
    driver.get(
        "http://sep.ucas.ac.cn/portal/site/226/xs/1/87B962125CB2D0C6FA8E3B03082C9D8BDA07DEF7528C7ADCBE4FD4B3DF3B6E70F0B731E9D6446375686330DE7CF9007B"
    )
    sleep(10)

    courses = []
    for i in driver.find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr"):
        try:
            c = [j.text for j in i.find_elements(By.TAG_NAME, "td")]
            c[0] = i.find_element(By.TAG_NAME, "a").get_attribute("href").split("/")[-1]
            courses.append(c)
        except Exception as e:
            print(e)
            pass
    return courses


def select_course(course, clabel, semester, is_major, cidx):
    driver.find_element(By.XPATH, "//a[contains(text(), '添加课程')]").click()

    sleep(1)

    driver.find_element(By.ID, "coursename").send_keys(course)

    select_element = driver.find_element(By.NAME, "CourseYears")
    select_element.find_element(By.XPATH, f"//option[text()='{semester}']").click()
    driver.find_element(By.ID, "search").click()

    sleep(1)

    entries = []
    for row in driver.find_element(By.ID, "divResult").find_elements(By.TAG_NAME, "tr"):
        try:
            entry = row.find_elements(By.TAG_NAME, "td")
            # print(entry)
            entries.append(
                (
                    entry[1].text,
                    entry[5]
                    .find_element(By.TAG_NAME, "a")
                    .get_attribute("href")
                    .split("/")[-1],
                    entry[0].find_element(By.TAG_NAME, "input"),
                )
            )
        except Exception as e:
            pass

    matches = []
    for label, idx, elem in entries:
        if label == clabel:
            matches.append((label, idx, elem))

    if len(matches) == 0:
        for label, idx, elem in entries:
            if label in clabel:
                matches.append((label, idx, elem))
    if len(matches) == 0:
        print("not found")
        return

    if len(matches) > 1:
        print("multiple matches")
        ok = False
        for label, idx, elem in matches:
            if cidx == idx or int(cidx.split("-")[0]) >= int(idx.split("-")[0]):
                print("found perfect match")
                ok = True
                elem.click()
                break
        if not ok:
            matches[0][2].click()

    if not is_major:
        driver.find_element(By.XPATH, '//input[@name="isxwk"]').click()

    for i in driver.find_elements(By.TAG_NAME, "button"):
        if "添加到我的课程计划" in i.text:
            i.click()
            break
    print("selected")


if __name__ == "__main__":
    login_sep("", "")
    courses = get_courses()

    driver.get("https://sep.ucas.ac.cn/portal/site/221/32")
    sleep(10)
    driver.get("https://py.ucas.ac.cn/zh-cn/training/zhidingkechengjihua/")
    sleep(10)
    for c in tqdm(courses):
        cidx = c[0]
        course = c[2]
        course = course.split("（")[0]
        clabel = c[1]
        semester = c[5].split(")")[0] + ")"
        is_major = c[4] == "是"
        print(course, clabel, semester, is_major, cidx)
        select_course(course, clabel, semester, is_major, cidx)
        sleep(1)

    driver.quit()
