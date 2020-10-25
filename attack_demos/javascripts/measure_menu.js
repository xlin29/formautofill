const webdriver = require('selenium-webdriver');
const chromium = require('/Users/linangelcat/Downloads/drivers/chromedriver1');

let driver = new webdriver.Builder()
    .forBrowser('chrome')
    .setChromeOptions(/* ... */)
    .setFirefoxOptions(/* ... */)
    .build();