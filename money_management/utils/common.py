import re


def cost_convert(cost_text):
    cost = int(cost_text.replace(" VND", "").replace(",", ""))
    # convert cost to string with dot separator
    cost = "{:,}".format(cost)
    return cost


def date_from_trans_date_time(trans_date_time, trans_time: bool = False):
    # trans date time format: 14:31 Chủ Nhật 19/05/2024
    # get last 10 characters
    date = trans_date_time[-10:]
    # current format: 19/05/2024 -> new format: 2024-05-19
    date = date[-4:] + "-" + date[3:5] + "-" + date[:2]
    if trans_time:
        # get first 5 characters
        time = trans_date_time[:5]
        # current format: 14:31 -> new format: 14:31:00
        time = time + ":00"
        # combine date and time
        date = date + " " + time
    return date


def get_value_from_mail_html_with_i_tag(mail_html: str, tag_value: str):
    # find first text match '<i>{tag_value}</i>' in html
    tag_start_pos = mail_html.find(f"<i>{tag_value}</i>")
    if tag_start_pos == -1:
        tag_start_pos = mail_html.find(f"<i>{tag_value} </i>")
    # find first open td tag after tag_value
    tag_start_pos = mail_html.find("<td", tag_start_pos)
    # find first text match '>' after tag_value
    tag_start_pos = mail_html.find(">", tag_start_pos)
    # find first close td tag after tag_value
    tag_end_pos = mail_html.find("</td>", tag_start_pos)
    # get tag value
    tag_value = mail_html[tag_start_pos + 1 : tag_end_pos]
    # trim start and end space
    tag_value = tag_value.strip()
    return tag_value


def valid_year_month(year_month):
    return re.match(r"\d{4}-\d{2}", year_month) is not None
