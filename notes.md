# Gen Notes #
 - Key bindings for Delete, Undo, and Redo are in wfd_drawing_widget

# Pending Questions #
 - Are the clickable subclasses and what not still being used?

## Need Settings Files ##
### wfd_select_manager.py 
 - Contains themes colors
### wfd_rendering_config.py
 - Contains graphics settings

### TODOs ###
 - In wfd_selection_manager, _apply_selection line ~142 is using hasattr, looks like
    looks like we can just add a setSelected or applySelect type function that performs
    the required operations based on the item type rather than this rediculous hasattr
    pattern thats being used
 - Does item type in wfd_select_manager need to be ENUM'd?
    Oh goodness does it look like its needed.. line ~194 and the isinstance mumbo
    jumbo is looking like it's going ot be an issue

# Stupid Ass hasattr Bandaids #
 - wfd_drawing_widget.py
    - line 94, 114
