# functions_prompts.py

from config import *

def get_pagination_params(args):
    try:
        page = int(args.get('page', 1))
        if page < 1: page = 1
    except (ValueError, TypeError):
        page = 1

    try:
        page_size = int(args.get('page_size', 10)) # Default to 10
        # Add reasonable limits to page size
        if page_size < 1: page_size = 10
        if page_size > 100: page_size = 100 # Max limit
    except (ValueError, TypeError):
        page_size = 10

    return page, page_size