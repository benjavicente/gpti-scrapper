import json
import re
from collections import defaultdict
from pathlib import Path
from typing import TypedDict

categories = [
    ["pasta", ["spaghetti", "macaroni", "lasagna", "rigati", "tallarines", "corbatas"]],
    ["salsa", ["tomate", "alfredo", "pesto", "salsa"]],
    ["arroz", ["arroz"]],
    ["aceite", ["aceite"]],
    ["legumbres", ["lentejas", "garbanzos", "frijoles", "porotos"]],
    ["sal", ["sal"]],
    ["harina", ["harina"]],
    ["crema", ["crema"]],
    ["queso", ["queso"]],
    ["huevo", ["huevo"]],
    ["pan", ["pan"]],
    ["carne", ["carne"]],
    ["pollo", ["pollo"]],
]

base_urls = {
    "jumbo": "https://www.jumbo.cl",
    "lider": "https://www.lider.cl",
    "lider-old": "https://www.lider.cl",
    "santaisabel": "https://www.santaisabel.cl",
}


class DataDict(TypedDict):
    price: str
    name: str
    link: str


amount_re = re.compile(r"(\d?\.?\d+)\s?(kg|g|l|ml)")


def transform_price(price: str, name: str):
    price_str = price.replace("$", "").replace(".", "")
    amount = 1
    current_name = name.lower()
    is_in_unit = False

    if "x" in price_str:
        units, _, price_str = price_str.partition("x")
        amount *= int(units)

    if (match := amount_re.search(current_name)) is not None:
        if match.group(2) in ("kg", "l"):
            amount *= 1000
        amount *= float(match.group(1))
        current_name = current_name.replace(match.group(0), "").strip(" ,")
        is_in_unit = True

    return {
        "name": current_name,
        "price": int(price_str),
        "cost": int(float(price_str) / amount),
        "is_in_unit": is_in_unit,
    }


def get_category_and_clean(data: DataDict, form_store: str):
    clean_data = transform_price(data["price"], data["name"])
    clean_data["link"] = base_urls.get(form_store, "") + data["link"]
    for category, keywords in categories:
        for keyword in keywords:
            if keyword in clean_data["name"]:
                return category, clean_data
    return None, clean_data


def main():
    data_path = Path("data")
    clean_data_path = Path("data-clean")
    clean_data_path.mkdir(exist_ok=True)

    cheapest_per_store = dict()
    analyzed_products_count = 0

    for data_file in data_path.glob("*.json"):
        grouped_by_category = defaultdict(list)

        # Get data from file
        with data_file.open() as f:
            for product_data in json.load(f):
                category, clean_data = get_category_and_clean(product_data, data_file.stem)
                if category is not None:
                    analyzed_products_count += 1
                    grouped_by_category[category].append(clean_data)

        # Get cheapest product
        cheapest = dict()
        for category, products in grouped_by_category.items():
            cheapest[category] = min(products, key=lambda x: x["cost"])

        # Save data
        cheapest_per_store[data_file.stem] = cheapest

    with clean_data_path.joinpath("all.json").open("w") as f:
        json.dump({"stores": cheapest_per_store, "count": analyzed_products_count}, f)


if __name__ == "__main__":
    main()
