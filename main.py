import os
import re
import time
import random
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

openGiveawaysLog = "open_giveaways.txt"
successfullyRemovedGiveawaysLog = "removed_giveaways.txt"
failedToRemoveGiveawaysLog = "failed_giveaways.txt"

chrome_install = ChromeDriverManager().install()
folder = os.path.dirname(chrome_install)
chromedriver_path = os.path.join(folder, "chromedriver.exe")
driver = webdriver.Chrome(chromedriver_path)

pastEnteredBooks = []
wantToReadTitles = []

def randomWait(seconds):
    driver.implicitly_wait(seconds)
    time.sleep(random.randint(1,10))

def readLoginInfo():
    with open("login.txt") as f:
        lines = f.readlines()
        username = lines[0][lines[0].index('=')+1:].strip()
        password = lines[1][lines[1].index('=')+1:].strip()
    return username, password

def facebookSignIn():
    username, password = readLoginInfo()

    driver.get("https://www.goodreads.com/user/sign_in")
    randomWait(5)
    facebookLogin = driver.find_element(By.XPATH, "//button[contains(@class, 'fbSignInButton')]")
    facebookLogin.click()
    randomWait(5)
    emailInputBox = driver.find_element(By.XPATH, "//input[@id='email']")
    emailInputBox.send_keys(username)
    passwordInputBox = driver.find_element(By.XPATH, "//input[@id='pass']")
    passwordInputBox.send_keys(password)
    loginButton = driver.find_element(By.XPATH, "//button[@id='loginbutton']")
    loginButton.click()
    randomWait(25)

def emailSignIn():
    username, password = readLoginInfo()

    driver.get("https://www.goodreads.com/user/sign_in")
    randomWait(5)
    emailLogin = driver.find_element(By.XPATH, "//button[contains(@class, 'authPortalSignInButton')]")
    emailLogin.click()
    emailInputBox = driver.find_element(By.XPATH, "//input[@name='email']")
    emailInputBox.send_keys(username)
    passwordInputBox = driver.find_element(By.XPATH, "//input[@name='password']")
    passwordInputBox.send_keys(password)
    loginButton = driver.find_element(By.XPATH, "//input[@id='signInSubmit']")
    loginButton.click()
    randomWait(25)

def readWantToReadShelf():
    booksOnPage = 1
    pageNumber = 1
    while booksOnPage > 0:
        driver.get(f"https://www.goodreads.com/review/list/14039716-emma?page={pageNumber}&per_page=50&ref=nav_mybooks&shelf=to-read&utf8=%E2%9C%93&view=table")
        randomWait(5)
        bookTitleElements = driver.find_elements_by_xpath("//tbody[@id='booksBody']/tr/td[@class='field title']/div/a")
        for bookTitleElement in bookTitleElements:
            wantToReadTitles.append(bookTitleElement.text)
        booksOnPage = len(bookTitleElements)
        pageNumber += 1

def readLogs():
    with open(openGiveawaysLog, "r") as f:
        for line in f:
            pastEnteredBooks.append(line)

def cleanLogs():
    # read each entry in the log and remove if it's past the end of the giveaway
    removeFromWantToRead = []
    with open(openGiveawaysLog, "w+") as f_open:
        for line in pastEnteredBooks:
            bookTitle, author, enteredBookDate, wantToRead = line.strip().split('\t')

            giveawayEndDateString = enteredBookDate.split('-')[1].strip() + " 2023"
            giveawayEndDate = datetime.datetime.strptime(giveawayEndDateString, "%b %d %Y").date()
            if giveawayEndDate >= datetime.date.today():
                f_open.write(line)
            else: # giveaway has expired
                if wantToRead == "False":
                    removeFromWantToRead.append((bookTitle, author))


    # check each title and remove from my "Want To Read Shelf" if it wasn't originally there
    with open(successfullyRemovedGiveawaysLog, "w+") as f_successful:
        with open(failedToRemoveGiveawaysLog, "w+") as f_failed:
            numBooksOnPreviousPages = 1
            pageNumber = 1
            nextPage = True
            while numBooksOnPreviousPages > 0:
                driver.get(f"https://www.goodreads.com/review/list/14039716-emma?page={pageNumber}&per_page=50&ref=nav_mybooks&shelf=to-read&utf8=%E2%9C%93&view=table")
                randomWait(5)
                numBooksOnPreviousPages = len(driver.find_elements_by_xpath("//tbody[@id='booksBody']/tr/td[@class='field title']/div/a"))
                for i in range(len(removeFromWantToRead)):
                    bookTitleToRemove = removeFromWantToRead[i][0]
                    bookAuthorToRemove = removeFromWantToRead[i][1]
                    try:
                        book = None
                        candidateBookTitles = driver.find_elements_by_xpath(f"//td[@class='field title']/div/a[contains(text(), \"{bookTitleToRemove}\")]")
                        for candidateBookTitle in candidateBookTitles:
                            if bookTitleToRemove in candidateBookTitle.text:
                                bookCandidate = candidateBookTitle.find_element_by_xpath('../../..')
                                authorOfCandidate = bookCandidate.find_element_by_xpath(f"./td[@class='field author']/div/a").text
                                hasFoundAuthors = True
                                for a in bookAuthorToRemove.split(' '):
                                    if a not in authorOfCandidate:
                                        hasFoundAuthors = False
                                if hasFoundAuthors:
                                    book = bookCandidate

                        if book != None:
                            deleteButton = book.find_element_by_xpath(".//a[@class='actionLinkLite smallText deleteLink']")
                            deleteButton.click()
                            randomWait(5)

                            # hit enter on the popup
                            # actions = ActionChains(driver)
                            # actions.send_keys(Keys.ENTER)
                            # actions.perform()
                            WebDriverWait(driver, 10).until(EC.alert_is_present())
                            driver.switch_to.alert.accept()
                            randomWait(5)

                            removeFromWantToRead[i] = ""
                            nextPage = False # stay on this page until you've gone through the list once and not found any books

                            print(f"{bookTitleToRemove} removed from 'Want to Read list'")
                            f_successful.write(bookTitleToRemove)
                    except Exception as e:
                        print(e)
                
                removeFromWantToRead = [book for book in removeFromWantToRead if book != ""]
                if nextPage:
                    pageNumber += 1
            
            for book in removeFromWantToRead:
                f_failed.writable(str.join(book, '\t') + "\n") 
            

def isBookNew(title):
    for book in pastEnteredBooks:
        enteredTitle = book.split('\t')[0]
        if title == enteredTitle:
            return False
    return True

def getImmediateText(element):
    OWN_TEXT_SCRIPT = "if(arguments[0].hasChildNodes()){var r='';var C=arguments[0].childNodes;for(var n=0;n<C.length;n++){if(C[n].nodeType==Node.TEXT_NODE){r+=' '+C[n].nodeValue}}return r.trim()}else{return arguments[0].innerText}"
    parent_text = driver.execute_script(OWN_TEXT_SCRIPT, element)
    return parent_text

def getDate(book):
    dates = book.find_element(By.XPATH, ".//span[@class='GiveawayMetadata__timeLeft']")
    datesText = getImmediateText(dates)
    datesText = ' '.join(datesText.split())
    return datesText

def logNewBook(book):
    with open(openGiveawaysLog, "a") as f:
        _RE_COMBINE_WHITESPACE = re.compile(r"\s+")

        bookTitle = book.find_element(By.XPATH, ".//h3[@class='Text Text__title3 Text__umber']/strong/a").text
        bookTitle = _RE_COMBINE_WHITESPACE.sub(" ", bookTitle).strip()
        if (bookTitle not in pastEnteredBooks):
            try:
                authors = book.find_element(By.XPATH, ".//h3[@class='Text Text__h3 Text__regular']/strong/a").text
            except:
                pass
            try:
                authors = book.find_element(By.XPATH, ".//h3[@class='Text Text__h3 Text__regular']/div/span/a").text
            except:
                pass
            authors = _RE_COMBINE_WHITESPACE.sub(" ", authors).strip()
            dates = getDate(book)

            wantToRead = bookTitle in wantToReadTitles

            pastEnteredBooks.append(f"{bookTitle}\t{authors}\t{dates}\t{wantToRead}\n")

            return True
        else:
            return False

def scrollIntoView(enterGiveawayButton):
    desired_y = (enterGiveawayButton.size['height'] / 2) + enterGiveawayButton.location['y']
    window_h = driver.execute_script('return window.innerHeight')
    window_y = driver.execute_script('return window.pageYOffset')
    current_y = (window_h / 2) + window_y
    scroll_y_by = desired_y - current_y
    driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_y_by)
    randomWait(5)

def enterGiveaway(book):
    # find the giveaway button, scroll it into view of the page, and click it
    enterGiveawayButton = book.find_element(By.XPATH, ".//div[@class='GiveawayMetadata__enterGiveawayButton']/a")
    scrollIntoView(enterGiveawayButton)
    enterGiveawayButton.click()
    randomWait(10)
    
    # switch to newly opened tab
    driver.switch_to.window(driver.window_handles[1])

    try:
        address = driver.find_element(By.XPATH, "//div[@class='addressOptions']/a[@class='addressLink']")
        address.click()
        randomWait(5)
        tosCheckbox = driver.find_element(By.XPATH, "//div[@class='stacked']/input")
        tosCheckbox.click()
        submitButton = driver.find_element(By.XPATH, "//input[@id='giveawaySubmitButton']")
        submitButton.click()
        randomWait(10)

        entrySuccess = True
    except:
        try:
            errorBox = driver.find_element(By.XPATH, "//div[@class='box noticeBox errorBox']")
            return "You have already entered this giveaway!" in errorBox.text
        except:
            entrySuccess = False
    
    # close new tab and switch back to the original
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return entrySuccess

def enterAllGiveawaysOnPage(giveaways_url):
    giveawayEntriesCount = 1

    while giveawayEntriesCount > 0:
        # navigate to giveaways page
        driver.get(giveaways_url)
        randomWait(15)

        # read all the giveawayEntries
        giveawayEntries = driver.find_elements_by_xpath("//div[@class='BookList']/article")
        giveawayEntriesCount = len(giveawayEntries)
        print("Number of giveaway books found: " + str(giveawayEntriesCount))
        for book in giveawayEntries:
            isNewBook = isBookNew(book)
            if isNewBook:
                enterGiveawaySuccess = enterGiveaway(book)
                if enterGiveawaySuccess:
                    logNewBook(book)

def main():
    try:
        emailSignIn()
        readWantToReadShelf()
        readLogs()
        enterAllGiveawaysOnPage(r"https://www.goodreads.com/giveaway/genre/Science%20fiction?sort=featured&format=print")
        enterAllGiveawaysOnPage(r"https://www.goodreads.com/giveaway/genre/Fantasy?sort=featured&format=print")
        cleanLogs()
    except Exception as e:
        print(e)
    finally:
        # close the drivers
        driver.quit()

if __name__=="__main__":
    main()