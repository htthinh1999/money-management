from enum import Enum


class Category(Enum):
    Food = "🍕 Ăn"
    Drink = "☕ Cà phê"
    Other = "💫 Khác"


def get_category_by_index(index):
    return list(Category)[index]


def get_category_by_string(category):
    return Category[category]
