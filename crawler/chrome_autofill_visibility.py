import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys
import hidden_detection as hidden
import re
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import os
from tqdm import tqdm
from stat import ST_CTIME, ST_MODE, S_ISDIR

timestr = str(time.strftime("%Y%m%d_%H%M%S"))
file = sys.argv[1]
start = int(sys.argv[2])
print(sys.argv[1])

try:
    chrome_invisible = open("hidden" + sys.argv[2] + ".json", 'a', encoding="utf-8")
    chrome_fields = open("fields" + sys.argv[2] + ".json", 'a', encoding="utf-8")
    chrome_all_visibility = open("visibility/visibility" + sys.argv[2] + ".json", 'a', encoding="utf-8")
except IOError:
    print("something went wrong opening output file.")
    assert False

# get urls from file
with open(file, 'r') as f:
    for line in f:
        line1 = json.loads(line)
        urls.append(line1['url'].strip())
print("-------processing--------", file)


class ProcessElement:
    def __init__(self, url):
        self.non_type = ['checkbox', 'button', 'radio', 'submit', 'file', 'image', 'search', 'hidden']
        self.types = ["text", "email", "tel", "number", "month", "password", "search", "url", "textarea"]
        self.url = url
        self.invisible = []
        self.fields_filled = []
        self.clickable = []
        self.all = []
        caps = DesiredCapabilities().CHROME
        caps["pageLoadStrategy"] = 'normal'  # complete
        binary_path = '**/chromium/src/out/Debug/Chromium.app/Contents/MacOS/Chromium'
        executable_path = '**/drivers/chromedriver1'
        print('driver: ', executable_path)
        # sort the profile by time to select the unused profile
        profile_path = '**/chromium_profiles/'
        profile_ls = (os.path.join(profile_path, fn) for fn in os.listdir(profile_path))
        profile_ls = ((os.stat(path), path) for path in profile_ls)
        profile_ls = ((stat[ST_CTIME], path) for stat, path in profile_ls if S_ISDIR(stat[ST_MODE]))
        profiles = [a[1] for a in sorted(profile_ls, key=lambda x: x[0])[:5]]
        for eachdirectory in profiles:  # if the profile is in use, try the other one
            print('profile: ', eachdirectory+'/')
            self.options = Options()
            self.options.headless = False
            self.options.add_experimental_option("prefs", {'profile.default_content_settings.popups': 2})
            self.options.add_experimental_option("prefs", {'profile.default_content_setting_values.notifications': 2})
            self.options.binary_location = binary_path
            self.options.add_argument('user-data-dir=' + eachdirectory+'/')
            self.options.add_argument('--no-sandbox')
            self.options.add_argument('--disable-dev-shm-usage')
            self.log_file = './chromium_logs/log' + sys.argv[2] + '_' + timestr + '.txt'
            try:
                self.driver = webdriver.Chrome(desired_capabilities=caps, chrome_options=self.options,
                                       executable_path=executable_path,
                                       service_args=['--verbose', '--log-path='+self.log_file])
                #self.driver.set_page_load_timeout(30)
                break
            except Exception as e:
                print(e)
                continue

    def visit_page(self):
        i = 0
        try:
            print('browsing page------', self.url)
            self.driver.get(self.url)
            self.detect_overlay()
            try:
                input_group = self.driver.find_elements_by_tag_name('input')
                select_group = self.driver.find_elements_by_tag_name('select')
                input_group.extend(select_group)
                input_group.reverse()
                i += 1
                print('page:', i, '# of inputs:', len(input_group))
                print('generating browsing logs---')
                for each_input in tqdm(input_group):
                    if each_input.get_attribute('type') not in self.types:
                        continue
                    for scroll_y in [-350, 0, 200]:
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", each_input)
                            self.driver.execute_script("window.scrollBy(arguments[0], arguments[1])", 0, scroll_y)
                            each_input.click()
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
                css_visibility = test_el.value_of_css_property('visibility')
                css_position = test_el.value_of_css_property('position')
                css_zindex = test_el.value_of_css_property('zIndex')
                test_width = self.driver.execute_script('return arguments[0].offsetWidth', test_el)
                test_height = self.driver.execute_script('return arguments[0].offsetHeight', test_el)
                if css_display != 'none' and css_visibility != "hidden" \
                        and any(word in css_position for word in ['fixed', 'absolute']) \
                        and css_zindex != 'auto'\
                        and test_width >= min_width and test_height >= min_height:
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
    # extract field info from driver logs
    # ------------------------------------------------
    def read_logs(self):
        print('parsing logs----')
        fields_after = set()
        fields_before = set()
        is_visible_pattern = re.compile(r'(?<=isvisible--)\d+')
        server_type_pattern = re.compile(r'(?<=server_type--)\d+')
        html_type_pattern = re.compile(r'(?<=html_type--)\d+')
        field_pattern = re.compile(r'(?<=result--).*')
        preview_pattern = re.compile(r'(?<=preview--).*')
        with open(self.log_file, 'r') as f_log:
            content = f_log.readlines()
        for each_line in content:
            if 'preview--' in each_line:
                fields_after.add(re.search(preview_pattern, each_line).group(0))
        for each_line in content:
            filled = {}
            if 'result--' in each_line:
                field_info = re.search(field_pattern, each_line).group(0)
                filled['type'] = re.search(server_type_pattern, each_line).group(0)
                filled['html_type'] = re.search(html_type_pattern, each_line).group(0)
                filled['is_visible'] = re.search(is_visible_pattern, each_line).group(0)
                filled['info'] = re.search(field_pattern, each_line).group(0)
                if field_info not in fields_before:
                    fields_before.add(field_info)
                    if field_info in fields_after:
                        self.fields_filled.append(filled)
                    self.all.append(filled)
        print('preview--', len(fields_after), 'autofilled--', len(self.fields_filled), 'all fields--', len(self.all))
        self.write_to_file(self.all, chrome_fields)

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
        id_pattern = re.compile(r"(?<=id_attribute=').*?(?=')")
        name_pattern = re.compile(r"(?<=name_attribute=').*?(?=')")
        class_pattern = re.compile(r"(?<=css_classes=').*?(?=')")
        autocomplete_pattern = re.compile(r"(?<=autocomplete=').*?(?=')")
        placeholder_pattern = re.compile(r"(?<=placeholder=').*?(?=')")
        id_attr = re.search(id_pattern, field['info']).group(0)
        name_attr = re.search(name_pattern, field['info']).group(0)
        class_attr = re.search(class_pattern, field['info']).group(0)
        autocomplete_attr = re.search(autocomplete_pattern, field['info']).group(0)
        placeholder_attr = re.search(placeholder_pattern, field['info']).group(0)
        attr_list = [['class', class_attr], ['autocomplete', autocomplete_attr], ['placeholder', placeholder_attr]]
        tag_list = ['input', 'select', 'textarea']
        try:
            if id_attr:
                el = self.locate_by_att('id', id_attr, attr_list, tag_list)
                if el:
                    return el
            elif name_attr:
                el = self.locate_by_att('name', name_attr, attr_list, tag_list)
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
                    visibility = 'hid_disp_none_itself'
                elif el.display_none_parent():
                    visibility = 'hid_disp_none_parent'
                elif el.visibility_hidden_itself():
                    visibility = 'hid_visi_hidden_itself'
                elif el.visibility_hidden_parent():
                    visibility = 'hid_visi_hidden_parent'
                elif el.size_hidden():
                    visibility = 'hid_size'
                elif el.off_screen():
                    visibility = 'hid_off_screen'
                elif el.transparent_itself():
                    visibility = 'hid_transparent_itself'
                elif el.transparent_parent():
                    visibility = 'hid_transparent_parent'
                elif el.clip_path_hidden():
                    visibility = 'hid_clip_path'
                elif el.ancestor_overflow_hidden():
                    visibility = 'hid_off_parents_overflow'
                elif el.covered_up():
                    visibility = 'hid_covered'
                elif el.clip_hidden():
                    visibility = 'hid_clipped_by_parent'
                elif not el.display and not el.click:
                    visibility = 'hid_other_reason'
                elif el.display and not el.click:
                    visibility = 'hid_clip_path'
                else:
                    visibility = 'visible'
        except Exception as exc:
            print(exc)
            pass
        return visibility

    def process_el(self):
        hid_flag = 0
        vis_flag = 0
        hid_types = set()
        self.fields_filled.reverse()
        for ind, field in enumerate(self.fields_filled):
            print('---', ind+1)
            input_el = self.locate_el(field)
            if not input_el:
                continue
            field['tag'] = input_el.tag_name
            field['visibility'] = self.calculate_visibility(input_el)
            if field['visibility']:
                if field['visibility'] != 'visible':
                    hid_flag = 1
                    hid_types.add(field['type'])
                    field = self.extract_comments(input_el, field)
                    self.driver.get_screenshot_as_file('screenshots/' + sys.argv[2] + '_' + timestr + '.png')
                else:
                    vis_flag = 1
                self.invisible.append(field)
                print(field['visibility'], field)
        if vis_flag and hid_flag:
            self.write_to_file(self.invisible, chrome_invisible)
            all_visibility = self.invisible
            self.all.reverse()
            print('start looking for corresponding visible ones')
            for ind, field in enumerate(self.all):
                if field['type'] not in hid_types:
                    continue
                print('---', ind + 1)
                if 'autofilled=0' in field['info']:
                    input_el = self.locate_el(field)
                    if not input_el:
                        continue
                    field['tag'] = input_el.tag_name
                    field['visibility'] = self.calculate_visibility(input_el)
                    all_visibility.append(field)
                    print(field['visibility'], field)
            self.write_to_file(all_visibility, chrome_all_visibility)


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
