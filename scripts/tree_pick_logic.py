import operator
import math
import asyncio
from joycontrol.controller_state import ControllerState, button_push, push_and_wait, l_stick_push, button_press, button_release

class TreePickLogic:
    def __init__(self, tree_grid_x = 0, tree_grid_y = 0, nook_grid = [0,0], inv_free_space = 0, inventory_total_space = 40):
        self.tree_grid_x = tree_grid_x #amount of trees x direction
        self.tree_grid_y = tree_grid_y #amount of trees in y direction
        self.nook_grid = nook_grid #position in [x,y] to travel to first before entering Nook's.
        # nook_grid needs to be exactly 2 spaces below where the actual building is to avoid running into building.
        self.inv_free_space = inv_free_space #free space in your inventory before running 'pick trees'
        self.total_trees = tree_grid_x * tree_grid_y
        self.inventory_total_space = inventory_total_space #total inventory space, defaults to fully upgraded amount of 40

    def secondary_defaults(self, fruit_in_pockets=0, trees_picked_total = 0, bells_in_wallet = 99000, move_speed=.31, current_grid_position = [0,0], current_direction = 'right'):
        self.move_speed = move_speed # amount of time to 'await asyncio.sleep' in order to move one grid space
        self.move_speed_default = move_speed # sets default move speed to allow for slightly changing self.move_speed later
        self.trees_picked_total = trees_picked_total #total number of trees picked
        self.trees_picked_current_row = 0 #number of trees picked so far in the current row
        self.tree_rows_picked = 1 #total number of tree rows that have been picked
        self.current_grid_position = current_grid_position #current grid position in [x,y], first tree picking position is at [0,0] first tree itself is at [1,0]
        self.current_direction = current_direction #current movement direction, set to 'right' or 'left' depending on your tree grid setup
        self.fruit_in_pockets = fruit_in_pockets #number of fruit in pockets, should get set back to 0 after selling
        self.nook_load_time = 12
        #calculate max amount of fruit that will safely fit in pockets
        safety_space = 3 #leave safety spaces for picking up random items like tree branches, acorns, weeds
        bells_in_wallet = bells_in_wallet #current amount of bells in wallet, defaults to 99000 to assume a full wallet
        bells_space = (self.total_trees * 1500) / 99000 #total amount of bell bags that will be generated when tree picking is done
        self.max_fruit = (self.inv_free_space - (safety_space + math.ceil(bells_space + (bells_in_wallet/99000)))) * 10

    async def turn(self, controller_state, direction, sec=0.5):
        await l_stick_push(controller_state, direction, (sec * self.move_speed))

    async def nook_shop_enter_exit(self, controller_state, enter_or_exit):
        if enter_or_exit == 'enter':
            await self.move_in_direction(controller_state, 'up', amount = 5)
            await push_and_wait(controller_state, 'a', self.nook_load_time, 'a', 1)
            await self.move_in_direction(controller_state, 'up', amount = 3)
            await asyncio.sleep(1)
            await self.turn(controller_state, 'left')
            await asyncio.sleep(1)
            await push_and_wait(controller_state, 'a', 5, 'a', 3, 'a', 5, 'a', 3)
            await asyncio.sleep(2)
        elif enter_or_exit == 'exit':
            await self.turn(controller_state, 'down')
            await asyncio.sleep(1)
            await self.move_in_direction(controller_state, 'down', amount = 6)
            await asyncio.sleep(1)
            await push_and_wait(controller_state, 'a', 2)
            await asyncio.sleep(self.nook_load_time)
            await self.move_in_direction(controller_state, 'down', amount = 2)
            await asyncio.sleep(2)
        else:
            print("Argument needs to be 'enter' or 'exit'")

    #turn to face tree, hit a to shake tree, pick fruit with y, walk around tree picking fruit
    async def pick_tree_and_move(self, controller_state, direction):
        if direction == 'right' or direction == 'left':
            await self.turn(controller_state, direction, sec = 0.7)
            await asyncio.sleep(0.8)
            await push_and_wait(controller_state, 'a', 2, 'y', 2)
            await self.turn(controller_state, 'down', sec = 0.55)
            await asyncio.sleep(0.5)
            await self.move_in_direction(controller_state, 'down', amount = 1)
            await asyncio.sleep(0.5)
            await self.turn(controller_state, direction, sec = 0.5)
            await asyncio.sleep(0.5)
            await self.move_in_direction(controller_state, direction, amount = 1)
            await push_and_wait(controller_state, 'y', 2)
            await self.move_in_direction(controller_state, direction, amount = 1)
            await asyncio.sleep(0.5)
            await self.turn(controller_state, 'up', sec = 0.75)
            await asyncio.sleep(0.5)
            await self.move_in_direction(controller_state, 'up', amount = 1)
            await push_and_wait(controller_state, 'y', 2)

            self.fruit_in_pockets += 3
            self.trees_picked_current_row += 1
            self.trees_picked_total += 1

        else:
            print("direction must be 'right' or 'left'")

        print("Total Trees Picked:")
        print(self.trees_picked_total)


    #amount here is grid spaces to move
    async def move_in_direction(self, controller_state, direction, amount = 0):

        if direction == 'up':
            self.current_grid_position[1] += amount
        elif direction == 'down':
            self.current_grid_position[1] -= amount
        elif direction == 'left':
            self.current_grid_position[0] -= amount
        elif direction == 'right':
            self.current_grid_position[0] += amount

        await l_stick_push(controller_state, direction, (amount * self.move_speed))
        await asyncio.sleep(1)
        print("Current Grid Position:")
        print(self.current_grid_position)
            
    #roundup to nearest 10th
    def roundup(self, x):
        return int(math.ceil(x / 10.0)) * 10

    #need to make sure to go all the way down to the confirm button before hitting plus, to ensure that inventory first space gets reset
    async def nook_shop_sell(self, controller_state):

        def sell_fruit():
            self.fruit_in_pockets -= 10
            if self.fruit_in_pockets < 0:
                self.fruit_in_pockets = 0

        #move to first inventory space. then set current inventory space counter
        inventory_move_to_first_space = (self.inventory_total_space - self.inv_free_space)

        #for now, this assumes the first open inventory space is in the first row
        for i in range(inventory_move_to_first_space):
            await push_and_wait(controller_state, 'right', 1)

        inventory_current_space = inventory_move_to_first_space + 1
        
        #determine current row
        selling_current_row = int(self.roundup(inventory_current_space) / 10)

        # while (self.fruit_in_pockets > 0) and (self.inventory_total_space - inventory_current_space) >= 0:
        while (self.inventory_total_space - inventory_current_space) >= 0:

            if self.roundup(inventory_current_space) - inventory_current_space > 0:
                # select 10 pieces of fruit, then move to next inventory space
                sell_fruit()
                await push_and_wait(controller_state, 'a', 'right')
             
            elif (self.inventory_total_space - inventory_current_space) >= 0:
                await push_and_wait(controller_state, 'a', 'right', 'down')
                
                sell_fruit()
                selling_current_row += 1

            inventory_current_space += 1
        #sell fruit
        await asyncio.sleep(2)
        await push_and_wait(controller_state, 'down', 1, 'down', 1, 'down', 1, 'down', 1, 'plus', 6, 'a', 5, 'a', 2, 'a', 4, 'a', 3)
        await asyncio.sleep(2)

    # When travelling to Nook's to_or_from = 'to' | travelling back from Nook's to_of_from = 'from'
    # might split these up into two functions to see if it helps with nook grid resetting itself
    async def nook_shop_travel(self, controller_state, to_or_from):

        

        if to_or_from == 'to':

            print("Grid before travel to")
            print(self.current_grid_position)

            #calculate movement amount towards Nook's based on current grid position
            #stores the absolute value of (current grid position - nook grid position) to use when travelling back in opposite direction

            self.grid_pos_difference = [0,0]
            self.grid_pos_difference[0] = (self.current_grid_position[0] - self.nook_grid[0])
            self.grid_pos_difference[1] = (self.current_grid_position[1] - self.nook_grid[1])

            if self.grid_pos_difference[1] < 0:
                self.direction_to_y = 'up'
                self.direction_from_y = 'down'
            elif self.grid_pos_difference[1] > 0:
                self.direction_to_y = 'down'
                self.direction_from_y = 'up'
            elif self.grid_pos_difference[1] == 0:
                self.direction_to_y = 'center'
                self.direction_from_y = 'center'
            
            if self.grid_pos_difference[0] < 0:
                self.direction_to_x = 'right'
                self.direction_from_x = 'left'
            elif self.grid_pos_difference[0] > 0:
                self.direction_to_x = 'left'
                self.direction_from_x = 'right'
            elif self.grid_pos_difference[0] == 0:
                self.direction_to_x = 'center'
                self.direction_from_x = 'center'

            #move down one, walk to first available space outside of tree line
            await self.turn(controller_state, 'down')
            await self.move_in_direction(controller_state, 'down', amount = 1)

            if self.direction_to_x == 'right':
                self.move_to_end_of_row = (self.tree_grid_x * 2) - self.current_grid_position[0]
                await self.turn(controller_state, 'right')
                await asyncio.sleep(1)
                await self.move_in_direction(controller_state, 'right', amount = self.move_to_end_of_row)
                await asyncio.sleep(1)
            else:
                self.move_to_end_of_row = self.current_grid_position[0]
                await self.turn(controller_state, 'left')
                await asyncio.sleep(1)
                await self.move_in_direction(controller_state, 'left', amount = self.move_to_end_of_row)
                await asyncio.sleep(1)

            #update grid position difference
            self.grid_pos_difference[0] = (self.current_grid_position[0] - self.nook_grid[0])
            self.grid_pos_difference[1] = (self.current_grid_position[1] - self.nook_grid[1])

            #adjust move speed for walking long distances
            self.move_speed = round((self.move_speed_default / 1.14),2)
            
            #move towards Nook's
            await self.turn(controller_state, self.direction_to_y)
            await asyncio.sleep(1)
            await self.move_in_direction(controller_state, self.direction_to_y, amount = abs(self.grid_pos_difference[1]))
            await asyncio.sleep(1)
            await self.turn(controller_state, self.direction_to_x)
            await asyncio.sleep(1)
            await self.move_in_direction(controller_state, self.direction_to_x, amount = abs(self.grid_pos_difference[0]))
            await asyncio.sleep(1)

            #set move speed back to default
            self.move_speed = self.move_speed_default

            print("Grid after travel to")
            print(self.current_grid_position)
            print("Nook grid after travel to")
            print(self.nook_grid)

        elif to_or_from == 'from':

            print("Grid before travel from")
            print(self.current_grid_position)
            print("Nook grid before travel from")
            print(self.nook_grid)
            #adjust move speed for walking long distances
            self.move_speed = round((self.move_speed_default / 1.14),2)
            #move back to grid position you travelled from
            await self.turn(controller_state, self.direction_from_x, sec = 0.7)
            await asyncio.sleep(1)
            await self.move_in_direction(controller_state, self.direction_from_x, amount = abs(self.grid_pos_difference[0]))
            await asyncio.sleep(1)
            await self.turn(controller_state, self.direction_from_y, sec = 0.7)
            await asyncio.sleep(1)
            await self.move_in_direction(controller_state, self.direction_from_y, amount = abs(self.grid_pos_difference[1]))
            await asyncio.sleep(1)
            await self.turn(controller_state, self.direction_from_x, sec = 0.7)
            await asyncio.sleep(1)
            await self.move_in_direction(controller_state, self.direction_from_x, amount = self.move_to_end_of_row)
            await asyncio.sleep(1)
            #set move speed back to default
            self.move_speed = self.move_speed_default
            await self.turn(controller_state, 'up', sec = 0.6)
            await self.move_in_direction(controller_state, 'up', amount = 1)
            await asyncio.sleep(1)

            print("Grid after travel from")
            print(self.current_grid_position)
            print("Nook grid after travel from")
            print(self.nook_grid)
            

    def change_direction(self):
        if self.current_direction == 'right':
            self.current_direction = 'left'
        elif self.current_direction == 'left':
            self.current_direction = 'right'

    async def tree_pick_loop(self, controller_state):

        #run this loop while there are still trees left to pick or there is still fruit in you pockets left to be sold
        while self.total_trees > self.trees_picked_total or self.fruit_in_pockets > 0:

            #Check if current row is even or odd and set direction appropriately
            # if abs((int(self.current_grid_position[1] / 2)) % 2) == 0:
                

            #While there are still trees left to pick in the current row, and the next tree will max out current inventory:
            #walk to Nook's, sell fruit, and walk back to current grid position
            while (self.tree_grid_x - self.trees_picked_current_row) > 0 and (self.fruit_in_pockets + 3) > self.max_fruit:
                
                await self.nook_shop_travel(controller_state, 'to')
                print("grid position before entering Nook's")
                print(self.current_grid_position)
                await self.nook_shop_enter_exit(controller_state, 'enter')
                await self.nook_shop_sell(controller_state)
                print("Fruit in pockets after selling")
                print(self.fruit_in_pockets)
                await self.nook_shop_enter_exit(controller_state, 'exit')
                print("grid position after leaving Nook's")
                print(self.current_grid_position)
                await self.nook_shop_travel(controller_state, 'from')

            if (self.tree_grid_x - self.trees_picked_current_row) > 0 and self.current_direction == 'right':
                await self.pick_tree_and_move(controller_state, 'right')
            elif (self.tree_grid_x - self.trees_picked_current_row) > 0 and self.current_direction == 'left':
                await self.pick_tree_and_move(controller_state, 'left')
                #else if there are no more trees left in the current row, but there are still more tree rows left, move down 2 spaces to the next row
            elif (self.tree_grid_x - self.trees_picked_current_row) == 0 and (self.tree_grid_y - self.tree_rows_picked) > 0:
                self.tree_rows_picked += 1
                self.trees_picked_current_row = 0
                await self.turn(controller_state, 'down', sec = .8)
                await asyncio.sleep(1)
                await self.move_in_direction(controller_state, 'down', amount = 2)
                self.change_direction()

                #else if there are no more trees and tree rows left, sell the last of your fruit
            else:
                await self.nook_shop_travel(controller_state, 'to')
                print("grid position before entering Nook's")
                print(self.current_grid_position)
                await self.nook_shop_enter_exit(controller_state, 'enter')
                await self.nook_shop_sell(controller_state)
                await self.nook_shop_enter_exit(controller_state, 'exit')
                print("grid position after leaving Nook's")
                print(self.current_grid_position)
                await self.nook_shop_travel(controller_state, 'from')