"""Complete, deterministic dummy papers used for export testing."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from core.format_loader import validate_format
from core.state_manager import PaperState


BIOLOGY_MCQ = [
    ("Which part of a plant absorbs water from soil?", ["Leaf", "Root", "Flower", "Fruit"], "Root"),
    ("Which organ pumps blood around the body?", ["Lung", "Heart", "Stomach", "Brain"], "Heart"),
    ("What do plants absorb to make food?", ["Oxygen", "Nitrogen", "Carbon dioxide", "Hydrogen"], "Carbon dioxide"),
    ("Which substance gives leaves their green colour?", ["Chlorophyll", "Haemoglobin", "Starch", "Protein"], "Chlorophyll"),
    ("Which bones protect the brain?", ["Ribs", "Skull", "Spine", "Pelvis"], "Skull"),
]

BIOLOGY_SHORT = [
    ("Define habitat and give one example.", "A habitat is the natural home of an organism, such as a pond for a frog."),
    ("Look at the plant diagram. State two functions of the stem.", "The stem supports leaves and transports water and food."),
    ("Explain photosynthesis briefly.", "Plants use sunlight, water and carbon dioxide to make food and release oxygen."),
    ("Name two organs in the digestive system and state one function of each.", "The stomach breaks down food; the small intestine absorbs nutrients."),
    ("Why do humans need to breathe?", "Breathing supplies oxygen for respiration and removes carbon dioxide."),
]

BIOLOGY_LONG = [
    ("Complete the observation table for a growing seed, then explain what a seed needs to germinate.", "A seed needs water, air and a suitable temperature to germinate."),
    ("Describe the path air takes from the nose to the lungs and explain gas exchange.", "Air passes through the nose, windpipe and bronchi into the lungs; oxygen enters blood and carbon dioxide leaves it."),
]

CHEMISTRY_MCQ = [
    ("Which solution is acidic?", ["Soap water", "Lemon juice", "Baking soda", "Salt water"], "Lemon juice"),
    ("What is the smallest unit of an element?", ["Molecule", "Atom", "Cell", "Crystal"], "Atom"),
    ("Which metal is liquid near room temperature?", ["Iron", "Copper", "Mercury", "Aluminium"], "Mercury"),
    ("What is the pH of a neutral solution?", ["0", "3", "7", "14"], "7"),
    ("What is the chemical formula of water?", ["H₂O", "CO₂", "O₂", "NaCl"], "H₂O"),
    ("Which change is reversible?", ["Burning paper", "Rusting iron", "Melting ice", "Cooking an egg"], "Melting ice"),
    ("Use the pH scale diagram. Which number is strongly acidic?", ["2", "7", "10", "14"], "2"),
    ("Which method separates sand from water?", ["Evaporation", "Filtration", "Magnetism", "Sublimation"], "Filtration"),
    ("Which gas is needed for iron to rust?", ["Oxygen", "Helium", "Neon", "Hydrogen"], "Oxygen"),
    ("An acid reacts with a base to form salt and what else?", ["Oxygen", "Water", "Carbon", "Iron"], "Water"),
]

CHEMISTRY_SHORT = [
    ("State two properties of acids.", "Acids taste sour and turn blue litmus red."),
    ("What is an element? Give one example.", "An element contains one kind of atom; oxygen is an example."),
    ("Explain the difference between melting and dissolving.", "Melting changes a solid to a liquid; dissolving spreads a substance through a solvent."),
    ("Fill the table with one use each for copper, iron and aluminium.", "Copper is used in wires, iron in structures and aluminium in cans."),
    ("Why is distilled water a poor conductor of electricity?", "It contains very few dissolved ions."),
    ("Name two ways to prevent rusting.", "Painting and galvanising keep water and oxygen away from iron."),
    ("What does a pH value below 7 indicate?", "It indicates an acidic solution."),
    ("Explain what a solute and solvent are.", "A solute dissolves in a solvent to form a solution."),
    ("Write the formula of carbon dioxide and water.", "CO₂ and H₂O."),
    ("Give one sign that a chemical reaction has occurred.", "A colour change, gas formation, or heat change may indicate a reaction."),
]

CHEMISTRY_LONG = [
    ("Compare physical and chemical changes with two examples of each.", "Physical changes include melting and freezing. Chemical changes include rusting and burning."),
    ("Explain neutralisation and give an everyday example.", "An acid and a base react to make salt and water; antacids neutralise excess stomach acid."),
    ("Describe how to separate a mixture of sand, salt and water.", "Filter out sand, then evaporate water to recover salt."),
    ("Explain the particle arrangement in solids, liquids and gases.", "Particles are tightly packed in solids, close but moving in liquids, and far apart in gases."),
]

SCIENCE_MCQ = [
    ("Which part of a cell controls its activities?", ["Nucleus", "Wall", "Vacuole", "Membrane"], "Nucleus"),
    ("Which force pulls objects toward Earth?", ["Friction", "Gravity", "Magnetism", "Tension"], "Gravity"),
    ("What is the SI unit of force?", ["Joule", "Newton", "Watt", "Pascal"], "Newton"),
    ("Which gas do plants release in photosynthesis?", ["Oxygen", "Carbon dioxide", "Nitrogen", "Methane"], "Oxygen"),
    ("What happens to water at 100 °C at normal pressure?", ["It freezes", "It boils", "It condenses", "It sublimes"], "It boils"),
    ("Which material conducts electricity well?", ["Rubber", "Wood", "Copper", "Glass"], "Copper"),
    ("Which organ filters blood to make urine?", ["Heart", "Kidney", "Liver", "Lung"], "Kidney"),
    ("Which energy source is renewable?", ["Coal", "Petroleum", "Solar", "Natural gas"], "Solar"),
    ("Which lens is thicker in the middle?", ["Concave", "Convex", "Plane", "Cylindrical"], "Convex"),
    ("Which state of matter has a fixed volume but no fixed shape?", ["Solid", "Liquid", "Gas", "Plasma"], "Liquid"),
    ("Which organism is a decomposer?", ["Fungus", "Grass", "Rabbit", "Eagle"], "Fungus"),
    ("What is the main source of energy for Earth?", ["Moon", "Sun", "Wind", "Ocean"], "Sun"),
    ("Which simple machine is a seesaw?", ["Pulley", "Lever", "Wheel", "Screw"], "Lever"),
    ("What is the pH of pure water?", ["2", "5", "7", "12"], "7"),
    ("Which blood cells carry oxygen?", ["White cells", "Red cells", "Platelets", "Plasma"], "Red cells"),
    ("Which process turns water vapour into liquid?", ["Evaporation", "Condensation", "Melting", "Freezing"], "Condensation"),
    ("Which planet is known for its rings?", ["Mars", "Venus", "Saturn", "Mercury"], "Saturn"),
    ("Which part of the ear detects sound vibrations?", ["Retina", "Eardrum", "Tongue", "Nostril"], "Eardrum"),
    ("Which substance is a good insulator?", ["Copper", "Aluminium", "Plastic", "Iron"], "Plastic"),
    ("What does a thermometer measure?", ["Mass", "Temperature", "Speed", "Volume"], "Temperature"),
]

SCIENCE_SHORT = [
    ("State two differences between plant and animal cells.", "Plant cells have a cell wall and chloroplasts; animal cells do not."),
    ("Explain why friction can be useful.", "Friction provides grip for walking and braking."),
    ("Define pressure and write its formula.", "Pressure is force per unit area: P = F/A."),
    ("What is respiration?", "Respiration releases energy from food in cells."),
    ("Describe evaporation in one sentence.", "Evaporation is the change of a liquid into vapour at its surface."),
    ("Name two conductors and two insulators.", "Copper and iron conduct; rubber and plastic insulate."),
    ("Use the circuit diagram to explain why the bulb lights.", "A closed circuit lets current flow through the bulb."),
    ("Give two advantages of solar energy.", "It is renewable and produces no direct air pollution."),
    ("What is the difference between reflection and refraction?", "Reflection bounces light back; refraction bends light between media."),
    ("Why can a liquid take the shape of its container?", "Its particles can move past one another."),
    ("What role do decomposers play in an ecosystem?", "They break down dead matter and return nutrients to soil."),
    ("Explain one way to conserve water at home.", "Repair leaks or collect rainwater for plants."),
    ("What is a lever? Give one example.", "A lever pivots around a fulcrum; a seesaw is an example."),
    ("How can litmus identify an acid?", "An acid turns blue litmus paper red."),
    ("State the function of red blood cells.", "They carry oxygen through the body."),
    ("Name the three states of water.", "Ice, liquid water and water vapour."),
    ("Why do we see phases of the Moon?", "We see different portions of the Moon's sunlit half."),
    ("Explain how sound reaches the inner ear.", "Sound vibrates the eardrum and middle ear bones."),
    ("Why is plastic used to cover electrical wires?", "Plastic insulates and helps prevent electric shock."),
    ("What is the normal unit for measuring temperature in school experiments?", "Degrees Celsius (°C)."),
]

SCIENCE_LONG = [
    ("Complete the results table and explain how light affects plant growth.", "Plants need light for photosynthesis, so growth is usually weaker without adequate light."),
    ("Describe an experiment to compare friction on smooth and rough surfaces.", "Pull the same block across each surface with a force meter and compare readings."),
    ("Use the energy-flow diagram to explain a simple food chain.", "Energy passes from the Sun to plants and then to consumers; some is lost at each step."),
    ("Explain the water cycle using evaporation, condensation and precipitation.", "Water evaporates, condenses into clouds and returns as precipitation."),
    ("Describe how a simple electric circuit works and draw its main parts.", "A cell, wires, switch and bulb form a closed path for current."),
    ("Compare acids and bases using indicators and two everyday examples.", "Acids turn blue litmus red; bases turn red litmus blue. Lemon juice is acidic and soap is basic."),
    ("Explain how the respiratory and circulatory systems work together.", "Lungs transfer oxygen to blood; the heart carries it to cells and returns carbon dioxide."),
    ("Discuss two causes of water pollution and two ways to reduce it.", "Sewage and industrial waste pollute water; treatment and careful disposal reduce pollution."),
]


SCENARIOS = {
    25: ("Biology", "6", "1 hour", 5, 5, 2, BIOLOGY_MCQ, BIOLOGY_SHORT, BIOLOGY_LONG),
    50: ("Chemistry", "7", "2 hours", 10, 10, 4, CHEMISTRY_MCQ, CHEMISTRY_SHORT, CHEMISTRY_LONG),
    100: ("Science", "8", "3 hours", 20, 20, 8, SCIENCE_MCQ, SCIENCE_SHORT, SCIENCE_LONG),
}


def _make_diagram(path: Path, title: str) -> str:
    image = Image.new("RGB", (480, 220), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, 472, 212), outline="#426b65", width=3)
    draw.text((24, 20), title, fill="#173a36")
    draw.line((60, 170, 420, 170), fill="#777777", width=3)
    for index, label in enumerate(("A", "B", "C")):
        x = 105 + index * 125
        draw.ellipse((x - 25, 100, x + 25, 150), outline="#2f8f83", width=4)
        draw.text((x - 5, 175), label, fill="#173a36")
    image.save(path)
    return str(path)


def build_scenario(marks: int, asset_dir: Path) -> tuple[dict, PaperState]:
    """Return a fully populated paper with exactly ``marks`` total marks."""
    subject, klass, duration, mcq_count, short_count, long_count, mcqs, shorts, longs = SCENARIOS[marks]
    asset_dir.mkdir(parents=True, exist_ok=True)
    fmt = {
        "format_id": f"dummy_{marks}_{subject.lower()}",
        "display_name": f"Dummy {marks}-mark {subject} paper",
        "school_name": "Sample School — Test Document",
        "subject": subject,
        "class": klass,
        "total_marks": marks,
        "duration": duration,
        "instructions": ["Answer all questions.", "Figures are for reference only.", "Marks are shown against each question."],
        "sections": [
            {"id": "A", "title": "Section A — Multiple Choice", "description": "Choose one answer.", "question_type": "MCQ", "marks_per_question": 1, "total_questions": mcq_count, "sub_parts": None},
            {"id": "B", "title": "Section B — Short Answer", "description": "Answer briefly.", "question_type": "short_answer", "marks_per_question": 2, "total_questions": short_count, "sub_parts": ["i", "ii"]},
            {"id": "C", "title": "Section C — Long Answer", "description": "Explain your answer.", "question_type": "long_answer", "marks_per_question": 5, "total_questions": long_count, "sub_parts": None},
        ],
        "docx_template": None,
    }
    validate_format(fmt)
    state = PaperState(fmt["format_id"])
    for number, (question, options, answer) in enumerate(mcqs, start=1):
        state.add_question("A", number, {"type": "MCQ", "text": question, "options": options, "answer": answer, "marks": 1})
    for number, (question, answer) in enumerate(shorts, start=1):
        state.add_question("B", number, {"type": "short_answer", "text": question, "answer": answer, "marks": 2})
    for number, (question, answer) in enumerate(longs, start=1):
        state.add_question("C", number, {"type": "long_answer", "text": question, "answer": answer, "marks": 5})

    # Exercise optional formatting and attachments in different combinations.
    if marks == 25:
        state.update_question("B", 2, {"image_path": _make_diagram(asset_dir / "plant.png", "Plant parts"), "image_position": "below", "image_width_pct": 65})
        state.update_question("B", 3, {"sub_parts": {"i": {"text": "Name the gas absorbed by plants.", "marks": 1}, "ii": {"text": "Name the gas released by plants.", "marks": 1}}})
        state.update_question("C", 1, {"table_def": {"rows": 3, "cols": 2, "headers": ["Condition", "Observation"]}})
    elif marks == 50:
        state.update_question("A", 7, {"image_path": _make_diagram(asset_dir / "ph_scale.webp", "pH scale"), "image_position": "alongside", "image_width_pct": 40})
        state.update_question("B", 4, {"table_def": {"rows": 4, "cols": 3, "headers": ["Metal", "Property", "Use"]}})
        state.update_question("B", 9, {"sub_parts": {"i": {"text": "Write the formula for water.", "marks": 1}, "ii": {"text": "Write the formula for carbon dioxide.", "marks": 1}}})
    else:
        state.update_question("B", 7, {"image_path": _make_diagram(asset_dir / "circuit.png", "Simple circuit"), "image_position": "below", "image_width_pct": 75})
        state.update_question("C", 3, {"image_path": _make_diagram(asset_dir / "energy_flow.jpg", "Energy flow"), "image_position": "alongside", "image_width_pct": 40})
        state.update_question("B", 12, {"table_def": {"rows": 3, "cols": 2, "headers": ["Water use", "Saving method"]}})
        state.update_question("C", 1, {"table_def": {"rows": 4, "cols": 3, "headers": ["Light", "Growth", "Notes"]}})
        state.update_question("B", 19, {"sub_parts": {"i": {"text": "Name one conductor.", "marks": 1}, "ii": {"text": "Name one insulator.", "marks": 1}}})
    return fmt, state
