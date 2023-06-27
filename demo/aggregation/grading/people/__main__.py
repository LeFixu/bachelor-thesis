from json import dumps
from .grade_people_extraction import get_grades_by_source


def default(obj):
    if hasattr(obj, "to_json"):
        return obj.to_json()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


if __name__ == "__main__":
    grades_by_src = get_grades_by_source()
    print("Result:")
    print(dumps(grades_by_src))
