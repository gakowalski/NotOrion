#! python -O
import random
import math

import pyglet

from globals import g
import masses
import utilities

def generate(count, edges):
	if count == 0:
		return []
	
	nebulae = []

	# minimize repetition of nebula colors
	lobe_primary_color_names = Lobe.color_names.keys()
	lobe_primary_color_index = random.randint(0, 1000)

	for coordinate in utilities.random_dispersed_coordinates(
		edges[0], edges[1], edges[2], edges[3],
		amount=count,
		dispersion=Nebula.max_offset*2
	):
		lobe_primary_color_index = lobe_primary_color_index % len(lobe_primary_color_names )
		primary_color_name = lobe_primary_color_names[lobe_primary_color_index]

		nebulae.append( Nebula(coordinate, primary_color_name) )
		
		# cycle to next lobe primary color
		lobe_primary_color_index += 1

	# ensure nebulae don't overlap
	min_nebula_distance = Nebula.max_offset * 2
	for nebula1 in nebulae:
		for nebula2 in nebulae:
			if nebula1 == nebula2:
				continue
			offset_from_zero = (
				abs(nebula1.coordinates[0] - nebula2.coordinates[0]), 
				abs(nebula1.coordinates[1] - nebula2.coordinates[1])
			)
			distance = math.sqrt(offset_from_zero[0]**2 + offset_from_zero[1]**2)
			if distance < min_nebula_distance:
				raise DataError, "at least two nebulae are not far enough apart"
	
	return nebulae

class Nebula(masses.Mass):
	"""A nebula. These interact with other objects, eg ships by slowing movement."""
	max_offset = 200
	min_lobes = 3
	max_lobes = 6
	lobe_offset_bounds = 80

	def __init__(self, coordinates, primary_color_name):
		super(Nebula, self).__init__(coordinates)

		if not Lobe.color_names.has_key(primary_color_name):
			raise DataError, "invalid primary color name: %s"%primary_color_name
		self.primary_color_name = primary_color_name

		number_of_lobes = random.randint(Nebula.min_lobes, Nebula.max_lobes)
		self.lobes = []
		permutation_index = random.randint(0,1000)

		for lobe_coordinate in utilities.random_dispersed_coordinates(
			-Nebula.lobe_offset_bounds, -Nebula.lobe_offset_bounds, 
				Nebula.lobe_offset_bounds, Nebula.lobe_offset_bounds,
			amount = number_of_lobes,
			dispersion = 15
		):

			# cycle through all lobe secondary/image combinations
			permutation_index += 1

			self.lobes.append( Lobe(lobe_coordinate, self.primary_color_name, permutation_index) )

		g.logging.debug("lobe count: %s", len(self.lobes))

class Lobe(object):
	# all lobe colors in one nebula center on either red, green, or blue in the color wheel:
	color_names = {
		'red': ['pink', 'yellow'],
		'green': ['cyan', 'yellow'],
		'blue': ['cyan', 'pink']
	}

	# load all available lobe image files; these will be used for collision detection
	# eg if a starship passes through them, it may have its speed reduced
	image_file_names = {}
	for primary in color_names.keys():
		for secondary in color_names[primary]:
			for image_number in [1,2]:
				id = '%s_%s_%d'%(primary, secondary, image_number)
				image_file_names[id] = '%s_%s_nebula_%d.png'%(primary, secondary ,image_number)

	# lobe image files have following naming convention:
	# {primary color}_{secondary color}_nebula_{permutation number}.png
	# example: blue_cyan_nebula_1.png

	# permutations for sequentially using all images
	# first element of tuples is secondary image index
	# second element of tuples is permutation number in file name
	# example: {primary color}_{color at index from first element}_{permutation number from second element}.png
	nebula_secondary_permutations = [
		(0, 1), (0, 2), (1, 1), (1, 2)
	]
	
	def __init__(self, coordinates, primary_color_name, permutation_index=None):
		self.coordinates = coordinates

		self.primary_color_name = primary_color_name

		if permutation_index is None:
			permutation_index = random.randint(0, len(Lobe.nebula_secondary_permutations))
		else:
			permutation_index = permutation_index % len(Lobe.nebula_secondary_permutations)
		(secondary_color_index, self.image_selector) = Lobe.nebula_secondary_permutations[permutation_index]

		self.secondary_color_name = Lobe.color_names[self.primary_color_name][secondary_color_index]

		self.rotation = random.randint(0,359)

		# use exponentiation to ensure floats less than 1.0 are as common as floats greater than 1.0
		self.scale = 10**random.uniform(-0.3, 0.3)

		image_id = '%s_%s_%d'%(self.primary_color_name, self.secondary_color_name, self.image_selector)
		self.pyglet_image_resource = pyglet.resource.image( Lobe.image_file_names[image_id] )