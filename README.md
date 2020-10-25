
# Privacy threats of browser form autofill

- [Extension](#Extension)
- [Attack Demos](#Attack-demos)
    - [Inter from multiple profiles](#Inter-from-multiple-profiles)
    - [Infer with 100k candidate values](#Infer-with-100k-candidate-values)
- [Crawler](#crawler)
- [Data](#data)
- [Research Paper](#Research-Paper)

## Extension
A chrome extension that detects autofillable, hidden elements in a visitied page. It shows a warning message on **lax mode**, and remove these hidden elements on **strict mode**.

## Attack demos
A novel, complicated side-channel attack that exploits browser’s autofill preview functionality to infer information in user's profile.

### Inter from multiple profiles

1. multiple_emails.html: obtain the email addresses from multiple profiles in the autofill

### Infer with 100k candidate values
1. preview_cc.html: infer user's credit card number (100k candidate values).

2. preview_phone.html: infer user's phone number (100k candidate values).

## Crawler
The crawler is ruuning on top of Selenium and an intrumented chromium/firefox.

## Data
In a crawl conducted during November 2019, these web pages were found to have hidden HTML elements autofilled by Chrome/Firefox.

## Research Paper
You can read more about the details of our work in the following research paper:

**Fill in the Blanks: Empirical Analysis of the Privacy Threats of Browser Form Autofill**

If you use our code, data, or otherwise conduct research related to our work, please cite our paper [PDF](https://www2.cs.uic.edu/~browser-autofill/files/autofill-ccs20.pdf):