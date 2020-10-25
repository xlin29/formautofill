import json
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import sys
import hidden_detection as hidden
import re
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
from tqdm import tqdm
import random
import copy
import os
from selenium.webdriver.common.keys import Keys

timestr = str(time.strftime("%Y%m%d_%H%M%S"))
print(timestr)
file = sys.argv[1]
ind = int(sys.argv[2])
print(sys.argv[1])

try:
    firefox_invisible = open("hidden/hidden" + sys.argv[2] + ".json", 'a', encoding="utf-8")
    firefox_autofill = open("autofill/fields" + sys.argv[2] + ".json", 'a', encoding="utf-8")
    firefox_all_visibility = open("all_visibility/fields" + sys.argv[2] + ".json", 'a', encoding="utf-8")
except IOError:
    print("something went wrong opening output file.")
    assert False


urls = []
with open(file, 'r') as f:
    for line in f:
        line1 = json.loads(line)
        urls.append(line1['url'].strip())
print("-------processing--------", file)


class ProcessElement:

    def __init__(self, url):
        self.non_type = ['checkbox', 'button', 'radio', 'submit', 'file', 'image', 'search', 'hidden']
        self.types = ["text", "email", "tel", "number", "month"]
        self.url = url
        self.invisible = []
        # all regex-matched input/select fields
        self.fields_all = []
        # auto-fillable input/select fields
        self.fields_filled = []
        self.clickable = []
        # initial driver
        caps = DesiredCapabilities().FIREFOX
        caps["pageLoadStrategy"] = "normal"  # complete
        binary_path = '**/mozilla-central/obj-x86_64-pc-linux-gnu/dist/bin/firefox'
        self.options = Options()
        self.options.headless = False
        self.options.set_preference("dom.push.enabled", False)
        self.options.set_preference("dom.webnotifications.enabled", False)
        self.options.binary_location = binary_path
        self.options.log.level = 'trace'
        self.log_file = './firefox_logs/log'+sys.argv[2]+'_'+timestr+'.txt'
        profile_path = '**/mozilla-central/obj-x86_64-pc-linux-gnu/tmp/'
        random.seed(ind)
        profile_nums = [str(i) for i in range(500)]
        ps = profile_path + 'profile'+random.choice(profile_nums)
        print(ps)
        try:
            self.driver = webdriver.Firefox(ps, desired_capabilities=caps, options=self.options,
                                            service_log_path=self.log_file)
        except Exception as e:
            print(e)
            pass

    # --------------------------------------------------------------
    # main function
    # visit page -> extract input/select fields -> generate browser logs -> calculate visibility of auto-fillable els
    # --------------------------------------------------------------
    def visit_page(self):
        i = 0
        try:
            print('browsing page------', self.url)
            self.driver.get(self.url)
            self.detect_overlay()
            try:
                input_group = self.driver.find_elements_by_tag_name('input')
                input_group.reverse()
                i += 1
                print('page:', i, '# of inputs:', len(input_group))
                print('generating browsing logs---')
                for each_input in tqdm(input_group):
                    if each_input.get_attribute('type') not in self.types and each_input.tag_name == 'input':
                        continue
                    for scroll_y in [-350, 0, 200]:
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", each_input)
                            self.driver.execute_script("window.scrollBy(arguments[0], arguments[1])", 0, scroll_y)
                            each_input.click()
                            each_input.click()
                            each_input.send_keys(Keys.DOWN)
                            # save the clickable els for detection part
                            self.clickable.append(each_input)
                            break
                        except:
                            continue
                self.read_logs()
                if self.fields_filled:
                    self.process_el()
            except:
                pass
        except Exception as exc:
            print(exc)
            pass
        try:
            self.driver.quit()
        except Exception as exc:
            print(str(exc))
            pass

    # ------------------------------------------------
    # identify if the el is root elements
    # ------------------------------------------------
    def not_root(self, test_el):
        return test_el.tag_name not in ['body', 'html'] and test_el != self.driver.execute_script('return document;')

    # ------------------------------------------------
    # find overlay/banner at the position
    # ------------------------------------------------
    def find_overlay(self, each_size, min_width, min_height, max_height):
        test_el = self.driver.execute_script('return document.elementFromPoint(arguments[0], arguments[1]);',
                                             each_size[0], each_size[1])
        if test_el and self.not_root(test_el):
            overlay = ''
            while not overlay and self.not_root(test_el):
                css_display = test_el.value_of_css_property('display')
                css_visibility = self.driver.execute_script('return getComputedStyle(arguments[0]).visibility;', test_el)
                css_position = self.driver.execute_script('return getComputedStyle(arguments[0]).position;', test_el)
                css_zindex = self.driver.execute_script('return getComputedStyle(arguments[0]).zIndex;', test_el)
                test_width = self.driver.execute_script('return arguments[0].offsetWidth', test_el)
                test_height = self.driver.execute_script('return arguments[0].offsetHeight', test_el)
                if css_display != 'none' and css_visibility != "hidden" \
                        and any(word in css_position for word in ['fixed', 'absolute']) \
                        and css_zindex != 'auto'\
                        and test_width >= min_width and min_height <= test_height:
                    try:
                        zindex_val = int(css_zindex)
                        if zindex_val >= 0:
                            overlay = test_el
                            print('overlay ', css_display, css_visibility, css_position, css_zindex, test_width,
                                  test_height)
                            overlay_single = self.is_single(overlay)
                            if overlay_single:
                                print('identify-overlay', overlay.tag_name,
                                      overlay.get_attribute('name'), overlay.get_attribute('id'))
                                return overlay_single
                    except:
                        pass
                test_el = test_el.find_element_by_xpath('..')
        return False

    # ------------------------------------------------
    # detect overlay at the center
    # detect banner at the bottom
    # ------------------------------------------------
    def detect_overlay(self):
        win_width = self.driver.execute_script('return window.innerWidth')
        win_height = self.driver.execute_script('return window.innerHeight')
        min_width = 100
        min_height = 100
        any_size = [[win_width / 2, win_height / 2, min_width, min_height], [win_width / 2, win_height / 3, min_width, min_height]]
        full_screen = [win_width / 2, win_height / 2, win_width - 50, win_height - 50]
        for each_size in any_size:
            overlay_el = self.find_overlay(each_size, min_width, min_height, win_height)
            if overlay_el:
                self.remove_overlay(overlay_el)  # remove immediately to detect more overlays
                overlay_el_full = self.find_overlay(full_screen, min_width, min_height, win_height)
                if overlay_el_full:
                    self.remove_overlay(overlay_el_full)
        #bottom_min_width = win_width
        #bottom_min_height = 50
        #bottom_size = [win_width / 2, win_height-50, bottom_min_width, bottom_min_height]
        #banner = self.find_overlay(bottom_size, bottom_min_width, bottom_min_height, 150)
        # if banner:
        #     self.remove_overlay(banner)

    # ------------------------------------------------
    # identify if the el is a single instance
    # ------------------------------------------------
    def is_single(self, el):
        while self.not_root(el):
            el_name = el.get_attribute('name')
            el_id = el.get_attribute('id')
            el_class = el.get_attribute('class')
            el_tag_name = el.tag_name
            try:
                if el_id:
                    print('overlay confirmed by id')
                    return el
                elif el_name:
                    if len(self.driver.find_elements_by_name(el_name)) == 1:
                        print('overlay confirmed by name')
                        return el
                    elif el_class:
                        if len(self.driver.find_elements_by_xpath
                                ("//" + el_tag_name + "[@class='" + el_class + "'][@name='" + el_name + "']")) == 1:
                            print('overlay confirmed by class and name')
                            return el
                elif len(self.driver.find_elements_by_xpath(("//" + el_tag_name + "[@class='" + el_class + "']"))) == 1:
                    print('overlay confirmed by class', el_class)
                    return el
                elif len(self.driver.find_elements_by_tag_name(el_tag_name)) == 1:
                    print('overlay confirmed by tag_name')
                    return el
                el = el.find_element_by_xpath('..')
            except Exception as exc:
                print(exc)
                pass
        return False

    # ------------------------------------------------
    # remove pop-up overlays or bottom banner
    # ------------------------------------------------
    def remove_overlay(self, overlay_el):
        # set global CSS
        self.driver.execute_script("arguments[0].setAttribute('style', 'display:none !important');", overlay_el)
        print('overlay removed')
        html_el = self.driver.find_element_by_tag_name('html')
        body_el = self.driver.find_element_by_tag_name('body')
        self.driver.execute_script("arguments[0].setAttribute('style', 'overflow:auto !important');", html_el)
        self.driver.execute_script("arguments[0].setAttribute('style', 'overflow:auto !important');", body_el)

    # ------------------------------------------------
    # create dict for each field
    # ------------------------------------------------
    def create_dict(self, field_text, fill_flag):
        field = {}
        typecount_pattern = re.compile(r'(?<=typecount--" ).*?(?= ")')
        filltype_pattern = re.compile(r'(?<=filltype--" ").*?(?=")')
        id_pattern = re.compile(r'(?<=id--" ").*?(?=")')
        name_pattern = re.compile(r'(?<=name--" ").*?(?=")')
        class_pattern = re.compile(r'(?<=class--" ").*?(?=")')
        autocomplete_pattern = re.compile(r'(?<=autocomplete--" ").*?(?=")')
        value_pattern = re.compile(r'(?<=value--" ").*?(?=")')
        tag_pattern = re.compile(r'(?<=tag--" ").*?(?=")')
        hidden_pattern = re.compile(r'(?<=hidden--" ).*?(?= )')
        option_num_pattern = re.compile(r'(?<=options-num--" )\d+')
        outerHTML_pattern = re.compile(r'(?<=outerHTML--" ").*(?=")')
        preview_val_pattern = re.compile(r'(?<=previewvalue--" ").*?(?=")')
        if not fill_flag:
            field['type_count'] = re.search(typecount_pattern, field_text).group(0)
        else:
            field['fill_val'] = re.search(preview_val_pattern, field_text).group(0)
        field['fill_type'] = re.search(filltype_pattern, field_text).group(0)
        field["id"] = re.search(id_pattern, field_text).group(0)
        field["name"] = re.search(name_pattern, field_text).group(0)
        field['class'] = re.search(class_pattern, field_text).group(0)
        field['autocomplete'] = re.search(autocomplete_pattern, field_text).group(0)
        field['hidden'] = re.search(hidden_pattern, field_text).group(0)
        field['tag'] = re.search(tag_pattern, field_text).group(0)
        if field['tag'] == 'SELECT':
            field['options_num'] = re.search(option_num_pattern, field_text).group(0)
        else:
            field['value'] = re.search(value_pattern, field_text).group(0)
            # print('value', value_text)
            # # firefox does NOT autofill <input> with value
            # if value_text and fill_flag:
            #     return False
        return field

    # ------------------------------------------------
    # extract field info from driver logs
    # ------------------------------------------------
    def read_logs(self):
        line_seen = set()
        print('parsing logs----')
        autofill_num_pattern = re.compile(r'(?<="autofill-num--" )\d+')
        autofill_num = 0
        elem_seen = set()
        with open(self.log_file, 'r', encoding="utf-8") as f_log:
            content = f_log.readlines()
        for each_line in content:
            each_line_text = each_line.encode('utf-8').decode('unicode_escape')
            if each_line_text in line_seen:
                continue
            else:
                line_seen.add(each_line_text)
                if 'autofill-num--' in each_line_text:
                    fill_num = re.search(autofill_num_pattern, each_line_text).group(0)
                    if fill_num:
                        autofill_num += int(fill_num)
                if 'field-matched--' in each_line_text:
                    field = self.create_dict(each_line_text, 0)
                    if field and field not in self.fields_all:
                        self.fields_all.append(field)
                        print('matched--', field)
                if 'preview--' in each_line_text:
                    filled = self.create_dict(each_line_text, 1)
                    print('preview--', filled)
                    if filled:
                        # identify an element by id, name, and type,
                        # in some cases, class of the same element can be different
                        filled_str = filled['id'] + filled['name'] + filled['fill_type']
                        if filled_str not in elem_seen:
                            elem_seen.add(filled_str)
                            self.fields_filled.append(filled)
        # the number can be different if the field has value
        print('all--', len(self.fields_all), 'autofill--', len(self.fields_filled), 'autofilled_num--', autofill_num)
        if len(self.fields_filled) > 0:
            self.write_to_file(self.fields_filled, firefox_autofill)

    def locate_by_att(self, attr, value, attr_list, tag_list):
        if attr == 'id':
            attr_els = self.driver.find_elements_by_id(value)
        else:
            attr_els = self.driver.find_elements_by_name(value)
        if len(attr_els) == 1:
            el = attr_els[0]
            print('element confirmed by ', attr)
            return el
        else:
            for attr_other in attr_list:
                for tag_name in tag_list:  # loop though possible tag_names
                    if attr_other[1]:
                        attr_els = self.driver.find_elements_by_xpath\
                            ("//" + tag_name + "[@" + attr + "='" + value + "']"
                             "[@" + attr_other[0] + "='" + attr_other[1] + "']")
                        if len(attr_els) == 1:
                            print('element confirmed by ', attr + ' and ', attr_other)
                            return attr_els[0]
        return False

    def locate_el(self, field):
        attr_list = [['class', field['class']], ['autocomplete', field['autocomplete']]]
        tag_list = ['input', 'select']  # autofillable tags by firefox
        try:
            if field['id']:
                el = self.locate_by_att('id', field['id'], attr_list, tag_list)
                if el:
                    return el
            elif field['name']:
                el = self.locate_by_att('name', field['name'], attr_list, tag_list)
                if el:
                    return el
            else:
                for attr in attr_list:
                    for tag_name in tag_list:
                        if attr[1]:
                            attr_els = self.driver.find_elements_by_xpath\
                                ("//" + tag_name + "[@" + attr[0] + "='" + attr[1] + "']")
                            if len(attr_els) == 1:
                                print('element confirmed by ', attr)
                                return attr_els[0]
        except Exception as exc:
            print(exc)
            pass
        return False

    # ------------------------------------------------
    # determine hidden elem and hidden reason
    # ------------------------------------------------

    def calculate_visibility(self, input_el):
        el = hidden.Detection(self.driver, input_el, self.clickable)
        el.print_out()
        visibility = ''
        try:
            if el.display and el.click:
                if el.size_hidden():
                    visibility = 'hid_size'
                else:
                    visibility = 'visible'
            else:
                if el.display_none_itself():  # display:none elem may return True for covered_up and off_screen function
                    visibility = 'hid_disp_none'
                elif el.display_none_parent():
                    visibility = 'hid_disp_none_parent'
                elif el.visibility_hidden_itself():
                    visibility = 'hid_visi_hidden'
                elif el.visibility_hidden_parent():
                    visibility = 'hid_visi_hidden_parent'
                elif el.size_hidden():
                    visibility = 'hid_size'
                elif el.off_screen():
                    visibility = 'hid_off_screen'
                elif el.transparent_itself():
                    visibility = 'hid_transparent'
                elif el.transparent_parent():
                    visibility = 'hid_transparent_parent'
                elif el.clip_path_hidden():
                    visibility = 'hid_clip_path'
                elif el.ancestor_overflow_hidden():
                    visibility = 'hid_off_parents_overflow'
                elif el.clip_hidden():
                    visibility = 'hid_clipped_by_parent'
                elif el.covered_up():
                    visibility = 'hid_covered'
                elif not el.display and not el.click:
                    visibility = 'hid_other_reason'
                else:
                    visibility = 'visible'
        except Exception as exc:
            print(exc)
            pass
        return visibility

    # ------------------------------------------------
    # determine hidden elem and hidden reason
    # ------------------------------------------------
    def process_el(self):
        hid_flag = 0
        vis_flag = 0
        hid_types = set()
        self.fields_filled.reverse()
        fields_filled = copy.deepcopy(self.fields_filled)
        for ind, field in enumerate(fields_filled):
            print('---', ind+1)
            input_el = self.locate_el(field)
            if not input_el:
                continue
            field['visibility'] = self.calculate_visibility(input_el)
            if field['visibility'] != 'visible':
                hid_flag = 1
                hid_types.add(field['fill_type'])
                field = self.extract_comments(input_el, field)
                self.driver.get_screenshot_as_file('screenshots/' + sys.argv[2] + '_' + timestr + '.png')
            elif field['visibility'] == 'visible' and field['tag'] != 'SELECT':
                vis_flag = 1
            self.invisible.append(field)
            print(field['visibility'], field)
        if vis_flag and hid_flag:
            self.write_to_file(self.invisible, firefox_invisible)
            all_visibility = []
            self.fields_all.reverse()
            print('start looking for corresponding visible ones')
            for index, field in enumerate(self.fields_all):
                # if field['fill_type'] not in hid_types:
                #     continue
                print('---', index + 1)
                # if field not in self.fields_filled:
                input_el = self.locate_el(field)
                if not input_el:
                    continue
                field['visibility'] = self.calculate_visibility(input_el)
                if field not in all_visibility:
                    all_visibility.append(field)
                    print(field['visibility'], field)
            self.write_to_file(all_visibility, firefox_all_visibility)

    def write_to_file(self, data, output_file):
        output = {}
        output['inputs'] = data
        output['url'] = self.url
        output_file.write(json.dumps(output, ensure_ascii=False) + '\n')
        output_file.flush()

    def extract_comments(self, el, field):
        comment_pattern = re.compile(r'(?<=<!--).*?(?=-->)')
        html_source = str(self.driver.page_source)
        source_ls = list(html_source.split('\n'))
        el_html = el.get_attribute('outerHTML')
        for i in range(len(source_ls)):
            if el_html in source_ls[i]:
                start_line = 0 if i < 5 else (i-5)
                comments_ls = re.findall(comment_pattern, ' '.join(source_ls[start_line:i]))
                if comments_ls:
                    field['comments'] = comments_ls
        return field


def main():
    for url in urls:
        case = ProcessElement(url)
        case.visit_page()


if __name__ == "__main__":
    main()
