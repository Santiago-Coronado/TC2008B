from random_agents.agent import RandomAgent, ObstacleAgent, RechargeStationAgent, TrashAgent
from random_agents.model import RandomModel

from mesa.visualization import (
    Slider,
    SolaraViz,
    make_space_component,
    make_plot_component,
)

from mesa.visualization.components import AgentPortrayalStyle

def random_portrayal(agent):
    if agent is None:
        return

    portrayal = AgentPortrayalStyle(
        size=50,
        marker="o",
    )

    if isinstance(agent, RandomAgent):
        if agent.dead:
            portrayal.color = "blue"
        else:
            portrayal.color = "red"
    elif isinstance(agent, ObstacleAgent):
        portrayal.color = "gray"
        portrayal.marker = "s"
        portrayal.size = 100
    elif isinstance(agent, RechargeStationAgent):
        portrayal.color = "green"
        portrayal.marker = "o"
    elif isinstance(agent, TrashAgent):
        portrayal.color = "brown"
        portrayal.marker = "x"

    return portrayal

def post_process_space(ax):
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


def post_process_lines(ax):
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.9))


# Define the colors for the line plot
COLORS_1 = {
    "Time": "orange",
    "Total Movements": "red",
}

COLORS_2 = {
    "Battery": "blue",
    "Percentage Clean": "green",
}

model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "num_agents": Slider("Number of agents", 10, 1, 50),
    "width": Slider("Grid width", 28, 1, 50),
    "height": Slider("Grid height", 28, 1, 50),
    "percentage_dirty": Slider("Percentage Dirty", 20, 0, 100),
    "percentage_obstacles": Slider("Percentage Obstacles", 10, 0, 100),
    "max_time": Slider("Max Time Steps", 1000, 100, 5000, 100),
}

# Create the model using the initial parameters from the settings
model = RandomModel(
    num_agents=model_params["num_agents"].value,
    width=model_params["width"].value,
    height=model_params["height"].value,
    seed=model_params["seed"]["value"]
)

# Create the space component
space_component = make_space_component(
    random_portrayal,
    draw_grid=False,
    post_process=post_process_space,
)

# Create the line plot component
lineplot_component_1 = make_plot_component(
    COLORS_1,
    post_process=post_process_lines,
)

lineplot_component_2 = make_plot_component(
    COLORS_2,
    post_process=post_process_lines,
)

# Create the SolaraViz page
page = SolaraViz(
    model,
    components=[space_component, lineplot_component_1, lineplot_component_2],
    model_params=model_params,
    name="Random Model",
)