import json
import json
import math
import matplotlib.pyplot as plt


class Signal_information(object):
    def __init__(self, signal_power: float, path: list):
        self._signal_power = signal_power
        self._noise_power = 0.0
        self._latency = 0.0
        self._path = path

    @property
    def signal_power(self):
        return self._signal_power

    def update_signal_power(self):
        return self._signal_power

    @property
    def noise_power(self):
        return self._noise_power

    @noise_power.setter
    def noise_power(self, noise_power: float):
        self._noise_power = noise_power

    def update_noise_power(self, increment: float):
        self._noise_power += increment

    @property
    def latency(self):
        return self._latency

    @latency.setter
    def latency(self, latency: float):
        self._latency = latency

    def update_latency(self, increment: float):
        self._latency += increment

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path: list):
        self._path = path

    def update_path(self):
        if self._path:
            self._path.pop(0)


class Node(object):
    def __init__(self, label: str, nodes: dict):
        self._label = label
        self._position = tuple(nodes['position'])
        self._connected_nodes = nodes['connected_nodes']
        self._successive = {}

    @property
    def label(self):
        return self._label

    @property
    def position(self):
        return self._position

    @property
    def connected_nodes(self):
        return self._connected_nodes

    @property
    def successive(self):
        return self._successive

    @successive.setter
    def successive(self, value: dict):
        self._successive = value

    def propagate(self, signal_info):
        signal_info.update_path()
        if signal_info.path:
            next_node_label = signal_info.path[0]
            if next_node_label in self._successive:
                self._successive[next_node_label].propagate(signal_info)


class Line(object):
    SPEED_OF_LIGHT = 3e8
    LIGHT_SPEED_IN_FIBER = SPEED_OF_LIGHT * 2 / 3

    def __init__(self, label: str, length: float):
        self._label = label
        self._length = length
        self._successive = {}

    @property
    def label(self):
        return self._label

    @property
    def length(self):
        return self._length

    @property
    def successive(self):
        return self._successive

    @successive.setter
    def successive(self, successive: dict):
        self.successive = successive

    def latency_generation(self) -> float:
        return self._length / self.LIGHT_SPEED_IN_FIBER

    def noise_generation(self, signal_power: float) -> float:
        return 1e-9 * signal_power * self._length

    def propagate(self, signal_info):
        # Update noise power and latency in signal information
        signal_info.update_noise_power(self.noise_generation(signal_info.signal_power))
        signal_info.update_latency(self.latency_generation())

        # Continue propagation to the next node if specified
        if signal_info.path:
            next_node_label = signal_info.path[0]
            if next_node_label in self._successive:
                self._successive[next_node_label].propagate(signal_info)


class Network(object):
    def __init__(self, nodes_file='nodes.json'):
        with open(nodes_file, 'r') as file:
            data = json.load(file)
        self._nodes = {}
        self._lines = {}

        for label, attributes in data.items():
            node = Node(label, attributes)
            self._nodes[label] = node

        for label, node in self._nodes.items():
            for connected_label in node.connected_nodes:
                line_label = label + connected_label
                if line_label not in self._lines:
                    length = self.calculate_distance(node.position, self._nodes[connected_label].position)
                    self._lines[line_label] = Line(line_label, length)

    def calculate_distance(self, pos1, pos2):
        return math.sqrt((pos2[0] - pos1[0]) ** 2 + (pos2[1] - pos1[1]) ** 2)

    @property
    def nodes(self):
        return self._nodes

    @property
    def lines(self):
        return self._lines

    def draw(self):
        plt.figure()
        for node in self._nodes.values():
            x, y = node.position
            plt.plot(x, y, 'bo')
            plt.text(x, y, node.label, fontsize=12, ha='right')

        for line in self._lines.values():
            start_node = line.label[0]
            end_node = line.label[1]
            x_values = [self._nodes[start_node].position[0], self._nodes[end_node].position[0]]
            y_values = [self._nodes[start_node].position[1], self._nodes[end_node].position[1]]
            plt.plot(x_values, y_values, 'k-')

        plt.xlabel('X Position (m)')
        plt.ylabel('Y Position (m)')
        plt.title('Network Topology')
        plt.show()

    # find_paths: given two node labels, returns all paths that connect the 2 nodes
    # as a list of node labels. Admissible path only if cross any node at most once
    def find_paths(self, start, end, path=[]):
        path = path + [start]
        if start == end:
            return [path]
        if start not in self._nodes:
            return []

        paths = []
        for node in self._nodes[start].connected_nodes:
            if node not in path:
                new_paths = self.find_paths(node, end, path)
                for new_path in new_paths:
                    paths.append(new_path)
        return paths

    # connect function set the successive attributes of all NEs as dicts
    # each node must have dict of lines and viceversa
    def connect(self):
        for line_label, line in self._lines.items():
            start_node = line_label[0]
            end_node = line_label[1]
            line.successive[end_node] = self._nodes[end_node]
            self._nodes[start_node].successive[line_label] = line

    # propagate signal_information through path specified in it
    # and returns the modified spectral information
    def propagate(self, signal_information):
        current_node_label = signal_information.path[0]

        while signal_information.path:
            current_node = self._nodes.get(current_node_label)
            if current_node is None:
                break

            # Update path in Signal_information
            signal_information.update_path()
            next_node_label = signal_information.path[0] if signal_information.path else None

            if next_node_label:
                # Identify the line between current and next node
                line_label = current_node_label + next_node_label
                line = self._lines.get(line_label)

                if line:
                    line.propagate(signal_information)
                    print(
                        f"Line {line_label}: Latency = {signal_information.latency}, Noise Power = {signal_information.noise_power}")

                current_node_label = next_node_label

        return signal_information
