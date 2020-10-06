class TreePickLogic:
    def __init__(self, tree_grid_x = 0, tree_grid_y = 0, nook_grid = [], inv_space = 0):
        self.tree_grid_x = tree_grid_x #amount of trees x direction
        self.tree_grid_y = tree_grid_y #amount of trees in y direction
        self.nook_grid = nook_grid #position of Tom Nook's store entrance, relative to first tree position at [0,0]
        self.inv_space = inv_space #free space in your inventory before running 'pick trees'

dummy_data = TreePickLogic(14, 24, [-7, -3], 40)

move_speed = .3 # amount of time to 'await asyncio.sleep' in order to move one grid space

total_trees = tree_grid_x * tree_grid_y
trees_picked_total = 0
trees_picked_current_row = 0
tree_rows_picked = 1
current_grid_position = [0,0]
current_direction = 'right'
current_row = 0
fruit_in_pockets = 0