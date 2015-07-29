
def displayed_dec(func):
    def wrapper(*args, **kwargs):
        items = func(*args, **kwargs)
        return filter(lambda x: x.is_displayed() and x.size['height'] * x.size['width'], items)
    return wrapper


def index_displayed(func):
    '''
    @return (index, WebElement)
    '''
    def wrapper(*args, **kwargs):
        items = func(*args, **kwargs)
        return filter(
            lambda (idx, x): x.is_displayed() and x.size[
                'height'] * x.size['width'],
            enumerate(items)
        )
    return wrapper

def _find_input(element):
    '''
    find input except `readonly` input
    '''
    if element.tag_name == 'input':
        return element
    _inputs = element.find_elements(By.XPATH, './/input[not(@readonly)]')
    if not _inputs:
        return None
    if len(_inputs) == 1:
        return _inputs[0]
    raise Exception("Too many input!")


def _set_input(element, value):
    if element.get_attribute('type') in INPUT_TEXT_TYPES:
        element.clear()
        element.send_keys(value)
    else:
        if value != element.is_selected():
            element.click()