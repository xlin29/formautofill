# Crawlers
The crawlers are running on top of Selenium and an intrumented Chromium (Version 81.0.4009.0) / Firefox (Nightly Version 74).

We made slight changes in browsers' source code to log the autofill information, including autofillable fields and autofill types.

## Chromimum:
1. As the crawler triggers the autofill preview function to log the autofill data,  we need to create a Chrome profile and use it from Selenium WebDriver. If we have multiple browser instances running in parallel, we then have multiple profiles.

### Build From Scratch
We provide source code as a patch to Chromium. Please follow these steps to instrument Chromium.

1. Check out Chromium source code from [`this repo`](#https://www.chromium.org/developers/how-tos/get-the-code) and follow all the steps to build Chromium.

2. Apply patch for Chromium checkout commit 0fd07ada07c6
    ```
    cd src
    git reset --hard 0fd07ada07c6
    git clean -fd
    git apply /PATH/TO/patches/autofill_diff.patch
    gclient sync
    Setup the build with gn command
    ```
3. Setup and compile
    ```
    gn gen out/Default
    autoninja -C out/Default
    ```


## Firefox
1. Changes in file `FormAutofillHeuristics.jsm`
    ```
     sectionCount++;
          }
        //inserted code
            let field1 = fieldDetail.elementWeakRef.get();
            let typecount = sectionCount;
            if (previousType == fieldDetail.fieldName){
                typecount++;
            }
                    if (field1.tagName == 'SELECT'){
                             console.log('field-matched---', 'typecount--',typecount, 'filltype--', fieldDetail.fieldName, 'tag--', field1.tagName, 'autocomplete--', field1.autocomplete,  'id--', field1.id, 'name--', field1.name, 'type--', field1.type, 'value--', field1.value, 'class--', field1.className, 'hidden--', field1.hidden, 'options-num--', field1.options.length);
                         }
                 else{
                      console.log('field-matched---', 'typecount--',typecount, 'filltype--', fieldDetail.fieldName, 'tag--',field1.tagName, 'autocomplete--', field1.autocomplete,  'id--', field1.id, 'name--', field1.name, 'type--', field1.type, 'value--', field1.value, 'class--', field1.className, 'readOnly--', field1.readOnly,'hidden--', field1.hidden, 'outerHTML--', field1.outerHTML);
                 }
           //code ends
    previousType = fieldDetail.fieldName;
    ```
2. changes in file `FormAutofillHandler.jsm`
    ```
    element.previewValue = value;
      //below is the inserted code
            
        var field1 = element;
             if (field1.tagName == 'SELECT'){
                 console.log('preview--', 'previewvalue--', value, 'filltype--',fieldDetail.fieldName, 'tag--', field1.tagName, 'autocomplete--', field1.autocomplete,  'id--', field1.id, 'name--', field1.name, 'type--', field1.type, 'value--', field1.value, 'class--', field1.className, 'hidden--', field1.hidden, 'options-num--', field1.options.length);
             }
             else{
                  console.log('preview--', 'previewvalue--', value,'filltype--', fieldDetail.fieldName, 'tag--',field1.tagName, 'autocomplete--', field1.autocomplete,  'id--', field1.id, 'name--', field1.name, 'type--', field1.type, 'value--', field1.value, 'class--', field1.className, 'readOnly--', field1.readOnly,'hidden--', field1.hidden, 'outerHTML--', field1.outerHTML);
             }
            
        //inserted code ends
    
    ```

## Crawling websites
1. chrome_autofill_visibility.py: crawler using chromium

2. firefox_autofill_visibility.py: crawler using firefox

3. hidden_detection.py: heuristics to detect hidden elements for different reasons.
