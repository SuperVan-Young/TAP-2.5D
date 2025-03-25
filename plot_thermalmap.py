import os
from argparse import ArgumentParser
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def read_heatmap(temperature_file, n_row, n_col):
	"""
	Read the temperature grid file from hotspot
	"""
	with open(temperature_file, 'r') as f:
		lines = f.readlines()    
	
	lines = [line.strip() for line in lines]
	lines = [line.split()[1] for line in lines if line]
	assert(len(lines) == n_row * n_col)

	temperature = np.zeros((n_row, n_col))

	for i in range(n_row):
		for j in range(n_col):
			temperature[i][j] = float(lines[i*n_col + j]) - 273.15

	return temperature


def read_floorplan(floorplan_file, n_row, n_col):
	"""
	Read the floorplan file
	"""
	units = []

	max_height = 0
	max_width = 0

	with open(floorplan_file, 'r') as file:
		for line in file:
			if line.strip() == '' or line.strip().startswith('#'):
				continue

			# the size should be normalized according to the grid size
			parts = line.strip().split('\t')
			unit = {
				'unit_name': parts[0],
				'width': float(parts[1]),
				'height': float(parts[2]),
				'left_x': float(parts[3]),
				'bottom_y': float(parts[4]),
				'specific_heat': None,
				'resistivity': None
			}

			# update the max height and width
			max_height = max(max_height, unit['height'] + unit['bottom_y'])
			max_width = max(max_width, unit['width'] + unit['left_x'])

			# only consider chiplets
			if not unit['unit_name'].startswith('Chiplet'):
				continue
			units.append(unit)

	# normalize the coordinates
	for unit in units:
		unit['left_x'] = unit['left_x'] / max_width * n_col
		unit['bottom_y'] = unit['bottom_y'] / max_height * n_row
		unit['width'] = unit['width'] / max_width * n_col
		unit['height'] = unit['height'] / max_height * n_row

	return units

def plot_heatmap_with_chiplets(heatmap, floorplan):
	"""
	Plot the heatmap and overlay the chiplets' outlines
	"""
	n_row, n_col = heatmap.shape
	chiplets = floorplan

	fig, ax = plt.subplots(figsize=(10, 8))

	# Plot the heatmap
	im = ax.imshow(heatmap, cmap='plasma', origin='lower', extent=[0, n_col, 0, n_row])
	plt.colorbar(im, label='Temperature (°C)')

	# Overlay the chiplets' outlines
	for chiplet in chiplets:
		left_x = chiplet['left_x']
		bottom_y = chiplet['bottom_y']
		width = chiplet['width']
		height = chiplet['height']

		rect = patches.Rectangle(
			(left_x, bottom_y), width, height,
			linewidth=1, edgecolor='white', facecolor='none'
		)
		ax.add_patch(rect)

		center = (left_x + width / 2, bottom_y + height / 2)
		ax.text(center[0], center[1], chiplet['unit_name'], color='white', ha='center', va='center', fontsize=16)

	# Set labels and title
	ax.set_xlabel('X Position')
	ax.set_ylabel('Y Position')
	ax.set_title('Heatmap with Chiplet Outlines')


def main(output_dir, n_row=64, n_col=64):
	temperature_file = None
	floorplan_file = None

	for file in os.listdir(output_dir):
		if file.endswith('.grid.steady'):
			temperature_file = os.path.join(output_dir, file)
		if file.endswith('ChipLayer.flp'):
			floorplan_file = os.path.join(output_dir, file)

	if temperature_file is None:
		raise FileNotFoundError("No file ending with '.grid.steady' found in the output directory.")
	if floorplan_file is None:
		raise FileNotFoundError("No file named 'ChipLayer.flp' found in the output directory.")


	heatmap = read_heatmap(temperature_file, n_row, n_col)
	floorplan = read_floorplan(floorplan_file, n_row, n_col)

	plot_heatmap_with_chiplets(heatmap, floorplan)

	plt.savefig(os.path.join(output_dir, 'thermalmap.png'))
	plt.clf()


def parse_args():
	parser = ArgumentParser(description='Plot the thermal map with chiplet outlines')
	parser.add_argument('-d', type=str, help='The output directory of the simulation')
	parser.add_argument('--n_row', type=int, default=64, help='Number of rows in the temperature grid')
	parser.add_argument('--n_col', type=int, default=64, help='Number of columns in the temperature grid')

	return parser.parse_args()


if __name__ == "__main__":
	args = parse_args()
	main(args.d, args.n_row, args.n_col)