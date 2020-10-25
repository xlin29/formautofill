# Heuristics to detect hidden elements for different reasons.

class Detection:

    def __init__(self, driver, el, clickable_els):
        self.driver = driver
        self.el = el
        self.display = self.el.is_displayed()
        self.click = False
        self.position = self.el.value_of_css_property('position')
        self.parent_el = self.el.find_element_by_xpath('..')
        self.driver.execute_script("arguments[0].scrollIntoView(true);", self.el)
        self.driver.execute_script("window.scrollBy(arguments[0], arguments[1])", 0, -350)
        boundingrec = self.driver.execute_script("return arguments[0].getBoundingClientRect()", self.el)
        self.el_width, self.el_height = boundingrec['width'], boundingrec['height']
        self.win_width = self.driver.execute_script('return window.innerWidth')
        self.win_height = self.driver.execute_script('return window.innerHeight')
        self.tag_name = self.el.tag_name
        print('processing--- ', self.el.get_attribute('id'), self.el.get_attribute('name'))
        print('width-height-x-y', self.el_width, self.el_height, boundingrec['x'], boundingrec['y'])
        if self.el in clickable_els:
            self.click = True
            print('clickable')
        else:
            try:
                self.el.click()
                self.click = True
            except Exception as exc:
                print(exc)
        
    def print_out(self):
        print('isdisplay', self.display)
        print('isclickable', self.click)

    # ------------------------------------------------
    # identify if the el is root elements
    # ------------------------------------------------
    def not_root(self, test_el):
        return test_el.tag_name not in ['body', 'html'] and test_el != self.driver.execute_script('return document;')

    # ------------------------------------------------
    # detect if the elem is off screen. consider elem_y >= win_innerheight when position is fixed or absolute.
    # notice display none is off screen due to 0 size.
    # if the element is position fixed, consider x >= self.win_width or y >= self.win_height
    # ------------------------------------------------
    def off_screen(self):
        print('testing off_screen----')
        boundingrec = self.driver.execute_script("return arguments[0].getBoundingClientRect()", self.el)
        x, y = boundingrec['x'], boundingrec['y']
        print('x-y-win.width-win.height', x, y, self.win_width, self.win_height)
        test_el = self.el
        while self.not_root(test_el):
            if self.position_fixed(test_el) and (x >= self.win_width or y >= self.win_height):
                return True
            test_el = test_el.find_element_by_xpath('..')
        return any([x + self.el_width <= 0,
                    y + self.el_height <= 0])
    
    # ------------------------------------------------
    # detect if the elem or its parent is display: none.
    # display: none elem is not consuming space in the layout. elem.size can be non-zero.
    # elem.offsetParent does not apply to fixed position.
    # ------------------------------------------------

    def display_none_itself(self):
        print('testing display_none----')
        display = self.el.value_of_css_property('display')
        if display == 'none':
            return True

    def display_none_parent(self):
        print('testing display_none of parent----')
        parent_el = self.parent_el
        while self.not_root(parent_el):
            if parent_el.value_of_css_property('display') == 'none':
                print('display_none_parent--', parent_el.tag_name, parent_el.get_attribute('id'),
                      parent_el.get_attribute('name'))
                return True
            parent_el = parent_el.find_element_by_xpath('..')
        return False

    # ------------------------------------------------
    # detect if the elem or its parent is visibility: hidden/collapse
    # ------------------------------------------------
    def visibility_hidden_itself(self):
        print('testing css visibility----')
        visibility = self.el.value_of_css_property('visibility')
        if visibility in ['hidden', 'collapse']:
            return True

    def visibility_hidden_parent(self):
        print('testing css visibility of parent----')
        parent_el = self.parent_el
        while self.not_root(parent_el):
            if parent_el.value_of_css_property('visibility') in ['hidden', 'collapse']:
                print('visi_hidden_parent--', parent_el.tag_name, parent_el.get_attribute('id'),
                      parent_el.get_attribute('name'))
                return True
            parent_el = parent_el.find_element_by_xpath('..')
        return False

    # ---------------------------------------------------------------------------------
    # detect if the elem or its parent is transparent
    # opacity is not inherited, but elem cannot be less transparent than the parent
    # we do NOT consider select tag,
    # select options cannot be fully transparent, because they are OS/browser dependent
    # ---------------------------------------------------------------------------------
    def transparent_itself(self):
        print('testing opacity----')
        if self.tag_name == 'select':
            return False
        opacity = float(self.el.value_of_css_property('opacity'))
        if opacity <= 0:
            parent_el = self.parent_el
            if parent_el.tag_name == 'label' and float(parent_el.value_of_css_property('opacity')) > 0:
                print('non-transparent label')
                return False
            elif float(parent_el.value_of_css_property('opacity')) > 0 and \
                    len(parent_el.find_elements_by_css_selector("*")) <= 2:
                print('non-transparent-parent')
                return False
            return True
        return False

    def transparent_parent(self):
        print('testing opacity of parent----')
        if self.tag_name == 'select':
            return False
        parent_el = self.parent_el
        while self.not_root(parent_el):
            if float(parent_el.value_of_css_property('opacity')) <= 0:
                print('transparent parent--', parent_el.tag_name, parent_el.get_attribute('id'),
                      parent_el.get_attribute('name'))
                return True
            parent_el = parent_el.find_element_by_xpath('..')
        return False


    def position_fixed_or_sticky(self, test_el):
        css_position = test_el.value_of_css_property('position')
        return any(word in css_position for word in ['fixed', 'sticky'])

    def is_descendant(self, test_el):
        return test_el in self.el.find_elements_by_xpath(".//*")
    # ---------------------------------------------------------------------------------------
    # detect if the elem is covered by another element
    # if the elem or ancestor do NOT have fixed or absolute position, it can't be covered
    # use the center point  instead of top-left
    # if top elem at the point is not the elem, not transparent, and has fixed|absolute position,
    # top elem is fixed, covered elem has to be fixed
    # top elem is absolute, covered elem cannot be fixed
    # display: none/visibility: hidden  will return True
    # there is no top elem for off_screen, clip-path_hidden, overflow, transparent
    # ---------------------------------------------------------------------------------------

    def covered_up(self):
        print('testing covered-up----')
        if self.click:
            return False
        boundingrec = self.driver.execute_script("return arguments[0].getBoundingClientRect()", self.el)
        x, y = boundingrec['x'], boundingrec['y']
        center_x = x + self.el_width/2
        center_y = y + self.el_height/2
        print('x-y-center.x-center.y', x, y, center_x, center_y)
        top_el = self.driver.execute_script('return document.elementFromPoint(arguments[0], arguments[1]);',
                                            center_x, center_y)
        if top_el and top_el != self.el and not self.is_descendant(top_el):
            while self.not_root(top_el):
                css_display = top_el.value_of_css_property('display')
                css_visibility = top_el.value_of_css_property('visibility')
                if css_display == 'none' or css_visibility in ['hidden', 'collapse']:
                    return False
                if self.position_fixed_or_absolute_or_relative(top_el):
                    if not self.not_effective_opacity(top_el):
                        position_top = top_el.value_of_css_property('position')
                        top_rec = self.driver.execute_script("return arguments[0].getBoundingClientRect()", top_el)
                        top_x, top_y, top_width, top_height = top_rec['x'], top_rec['y'], \
                            top_rec['width'], top_rec['height']
                        print('top_x, top_y, top_width, top_height', top_x, top_y, top_width, top_height)
                        # we need to allow small deviation(-2),
                        # some cases result in false negatives as users cannot see it with small deviation
                        if top_x + top_width >= x + self.el_width - 2 and top_y + top_height >= y + self.el_height - 2:
                            # in case popup shows late
                            pop_str = ''
                            for value in [top_el.get_attribute('class'), top_el.get_attribute('name'),
                                          top_el.get_attribute('id')]:
                                value = str('0' if not value else value)
                                pop_str += value + ' '
                            # it may be covered by picker from other input fields
                            if any(word in pop_str for word in ['popup', 'picker']):
                                print('covering element is POPUP or PICKER')
                                return False
                            print('coverd by--', pop_str, top_el.value_of_css_property('position'))
                            break
                        else:
                            print(top_el.get_attribute('class'), top_el.value_of_css_property('position'),
                                  top_el.get_attribute('name'), top_el.get_attribute('id'), 'is too small to cover')
                            return False
                    else:
                        self.click = True
                        print('unclickable but visible due to low opacity of cover')
                        return False
                top_el = top_el.find_element_by_xpath('..')
            else:
                print('top_el not position fixed|absolute or transparent')
                return False
            if top_el.tag_name == 'label' and len(top_el.find_elements_by_xpath(".//*")) == 0:
                print('top_el is the label for', top_el.get_attribute('for'))
                self.click = True
                return False
            else:
                return True
            # test_el = self.el
            # fixed_flag = 0
            # while self.not_root(test_el):
            #     css_position = test_el.value_of_css_property('position')
            #     if 'fixed' in css_position:
            #         fixed_flag = 1
            #         break
            #     test_el = test_el.find_element_by_xpath('..')
            # if any(['fixed' in position_top and fixed_flag, 'fixed' not in position_top and not fixed_flag]):
            #     # self.remove_cover(top_el) # removing the cover may affect following elements
            #     return True
        return False


    def not_effective_opacity(self, test_el):
        while self.not_root(test_el):
            opacity = float(test_el.value_of_css_property('opacity'))
            if opacity < 1:
                print('transparent cover--', test_el.get_attribute('outerHTML'))
                return True
            test_el = test_el.find_element_by_xpath('..')
        return False

    # --------------------------------------------------------------
    # for select field, if any option is visible, it is visible
    # --------------------------------------------------------------
    def examine_select(self):
        if self.tag_name == 'select':
            return True
        # no need to check option here as it takes too much time and the results are not useful
        #     options = self.el.find_elements_by_xpath(".//option")
        #     for each in options:
        #         try:
        #             each.click()
        #             print('visible-option', each.get_attribute('outerHTML'))
        #             return True
        #         except:
        #             continue
        return False

    # ------------------------------------------------
    # remove the top element to show the covered element
    # ------------------------------------------------
    def remove_cover(self, top_el):
        self.driver.execute_script("arguments[0].setAttribute('style', 'display:none !important');", top_el)
        print('top_el removed')
        try:
            self.el.click()
            print('the element can be clicked now')
        except Exception as exc:
            print(exc)
            pass

    def position_fixed_or_absolute(self, test_el):
        css_position = test_el.value_of_css_property('position')
        return any(word in css_position for word in ['fixed', 'absolute'])

    def position_fixed_or_absolute_or_relative(self, test_el):
        css_position = test_el.value_of_css_property('position')
        return any(word in css_position for word in ['fixed', 'absolute', 'relative'])

    def position_fixed(self, test_el):
        css_position = test_el.value_of_css_property('position')
        return 'fixed' in css_position

    def overflow_hidden(self, test_el):
        css_overflow = [test_el.value_of_css_property('overflow'), test_el.value_of_css_property('overflow-y'),
                        test_el.value_of_css_property('overflow-x')]
        return 'hidden' in css_overflow

    # -------------------------------------------------------------------------------------------
    # detect if the elem is hidden by ancestor
    # if ancestor has hidden overflow properties and not effective size
    # if any element between el and ancestor(not included) are not fixed or absolute position
    # --------------------------------------------------------------------------------------------
    def ancestor_overflow_hidden(self):
        print('testing ancestor_overflow_hidden----')
        parent_el = self.parent_el
        test_el = self.el
        while self.not_root(parent_el):
            if self.overflow_hidden(parent_el) and self.not_effective_size(parent_el):
                ancestor = parent_el
                print('overflow-ancestor', ancestor.get_attribute('id'))
                break
            parent_el = parent_el.find_element_by_xpath('..')
        else:
            return False
        while test_el != ancestor:
            if self.position_fixed_or_absolute(test_el):
                return False
            test_el = test_el.find_element_by_xpath('..')
        else:
            return True

    # -------------------------------------------------------------------------------------------
    # detect if the elem is out of the bounds of ancestor's overflow
    # if ancestor has hidden overflow properties
    # offset parent is the closest parent with position relative, absolute, or fixed
    # if offset parent is a parent of the ancestor and elem's position is not relative, not clip
    # if offset parent is a child of the ancestor and offset parent's position is absolute, not clip
    # --------------------------------------------------------------------------------------------
    def clip_hidden(self):
        print('testing clip_hidden----')
        offset_parent_el = self.driver.execute_script("return arguments[0].offsetParent", self.el)
        parent_el = self.parent_el
        if not self.not_root(parent_el):
            return False
        while self.not_root(parent_el):
            if self.overflow_hidden(parent_el):
                ancestor = parent_el
                print('ancestor-clip', ancestor.get_attribute('id'), ancestor.value_of_css_property('position'))
                break
            parent_el = parent_el.find_element_by_xpath('..')
        else:
            return False
        if ancestor.tag_name == 'label':
            print('label for ', ancestor.get_attribute('class'))
            return False
        if offset_parent_el:
            print('offset-parent', offset_parent_el.get_attribute('class'), offset_parent_el.get_attribute('name'),
                  offset_parent_el.get_attribute('id'), offset_parent_el.tag_name,
                  offset_parent_el.value_of_css_property('position'))
            if self.is_child(offset_parent_el, ancestor) and \
                    'relative' not in self.position:
                print('offset is parent of ancestor but el is not relative')
                return False
            # if self.is_child(ancestor, offset_parent_el) and \
            #         'absolute' in offset_parent_el.value_of_css_property('position'):
            #     print('offset is the child of ancestor and it is absolute')
            #     return False
            if self.is_child(ancestor, offset_parent_el) and \
                    'absolute' not in ancestor.value_of_css_property('position'):
                print('offset is the child of ancestor and ancestor is not absolute')
                return False
        ancestor_rec = self.driver.execute_script("return arguments[0].getBoundingClientRect()", ancestor)
        ancestor_x, ancestor_y, ancestor_width, ancestor_height = \
            ancestor_rec['x'], ancestor_rec['y'], ancestor_rec['width'], ancestor_rec['height']
        boundingrec = self.driver.execute_script("return arguments[0].getBoundingClientRect()", self.el)
        x, y = boundingrec['x'], boundingrec['y']
        return any([x > ancestor_x + ancestor_width,
                    x + self.el_width < ancestor_x,
                    y > ancestor_y + ancestor_height,
                    y + self.el_height < ancestor_y])

    def is_child(self, parent_el, child_el):
        while self.not_root(child_el):
            if parent_el == child_el:
                return True
            child_el = child_el.find_element_by_xpath('..')
        return False

    # ------------------------------------------------
    # detect elem hidden by clip-path
    # ------------------------------------------------
    def clip_path_hidden(self):
        print('testing clip_path_hidden----')
        digit_pattern = re.compile(r'\d+')
        parent_el = self.el
        while self.not_root(parent_el):
            clip_path = parent_el.value_of_css_property('clip-path')
            if clip_path:
                digits = re.findall(digit_pattern, clip_path)
                if digits:
                    digits = [int(i) for i in digits]
                    digits_sum = sum(digits)
                    print("clip-path", clip_path, digits)
                    if digits_sum == 0:
                        return True
            parent_el = parent_el.find_element_by_xpath('..')
        return False

    # ------------------------------------------------
    # detect if the elem has been set to width/height <=0
    # ------------------------------------------------
    def size_hidden(self):
        print('testing effective_size----')
        if self.el_width <= 0 or self.el_height <= 0:
            return True
        return False

    # ------------------------------------------------
    # has no effective width or height
    # ------------------------------------------------
    def not_effective_size(self, test_el):
        rec = self.driver.execute_script("return arguments[0].getBoundingClientRect()", test_el)
        test_width, test_height = rec['width'], rec['height']
        if test_height <= 0 or test_width <= 0:
            print('size--', test_height, test_width)
            return True
        else:
            return False

    # ------------------------------------------------
    # has no effective width or height
    # ------------------------------------------------
    def has_clip_path(self):
        parent_el = self.el
        while self.not_root(parent_el):
            clip_path = parent_el.value_of_css_property('clip-path')
            if clip_path:
                print('clip_path--', clip_path)
                return True
            else:
                parent_el = parent_el.find_element_by_xpath('..')
        return False
