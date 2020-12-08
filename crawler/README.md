# Crawler
The crawler is runing on top of Selenium and an intrumented chromium/firefox.

We made slight changes in browsers' source code to log the autofill information, including autofillable fields and autofill types.

## Chromimum:
1. As the crawler triggers the autofill preview function to log the autofill data,  we need to create a Chrome profile and use it from Selenium WebDriver. If we have multiple browser instances running in parallel, we then have multiple profiles.

2. Make chromium automatically select the first autofill profile. In method `autofill_popup_controller_impl.cc` of source code file `autofill_popup_controller_impl.cc`, set:
```
autoselect_first_suggestion = true;
```
3. Log autofill preview information.
In method `PreviewFormField` of source code file `form_autofill_util.cc`, insert code:
```
LOG(WARNING) << "preview---" << data;
```
4. In method `AutofillManager::FillOrPreviewDataModelForm` of souce code file `autofill_manager.cc`, insert code:
```
int field_len = result.fields.size();
    LOG(WARNING) << field_len;
    for (int i =0; i < field_len; i++){
        LOG(WARNING) << "isvisible--" << form_structure->field(i)->IsVisible() <<" html_type--"<<form_structure->field(i)->Type().html_type() << " server_type--"<<form_structure->field(i)->server_type() << "result--" << result.fields.at(i);
       }
```
5. Comment out the following code in file `autofill_manager.cc` for chromium to autofill fields of company type.
```
if (got_autofillable_form && context->focused_field->Type().GetStorableType() == COMPANY_NAME && !base::FeatureList::IsEnabled(features::kAutofillEnableCompanyName)) {
    got_autofillable_form = true;
  }
```
```
if (field_group_type == COMPANY &&
        !base::FeatureList::IsEnabled(features::kAutofillEnableCompanyName)) {
      continue;
    }
```
## Firefox
1. changes in file `FormAutofillHeuristics.jsm`
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
