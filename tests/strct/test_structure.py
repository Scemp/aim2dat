"""Test Structure class."""

# Standard library imports
import os

# Third party library imports
import pytest
import numpy as np
from openmm import LangevinMiddleIntegrator
from openmm.app import ForceField

# Internal library imports
from aim2dat.strct import Structure, SamePositionsError
from aim2dat.io import read_yaml_file
from aim2dat.ext_interfaces.openmm import _get_potential_energy


STRUCTURES_PATH = os.path.dirname(__file__) + "/structures/"
ZEO_PATH = os.path.dirname(__file__) + "/zeo/"
IO_PATH = os.path.dirname(__file__) + "/io/"


def test_structure_print():
    """Test print statement of Structure class."""
    strct_dict = read_yaml_file(STRUCTURES_PATH + "Cs2Te_62_prim_kinds.yaml")
    structure = Structure(**strct_dict, label="test")
    assert structure.__str__() == (
        "----------------------------------------------------------------------\n"
        "-------------------------- Structure: test ---------------------------\n"
        "----------------------------------------------------------------------\n"
        "\n"
        " Formula: Cs8Te4\n"
        " PBC: [True True True]\n"
        "\n"
        "                                 Cell                                 \n"
        " Vectors: - [  9.5494   0.0000   0.0000]\n"
        "          - [  0.0000   5.8913   0.0000]\n"
        "          - [  0.0000   0.0000  11.6228]\n"
        " Lengths: [  9.5494   5.8913  11.6228]\n"
        " Angles: [ 90.0000  90.0000  90.0000]\n"
        " Volume: 653.8719\n"
        "\n"
        "                                Sites                                 \n"
        "  - Cs Cs1   [  3.3518   4.4185   0.8543] [  0.3510   0.7500   0.0735]\n"
        "  - Cs Cs1   [  0.2406   1.4728   2.0224] [  0.0252   0.2500   0.1740]\n"
        "  - Cs Cs1   [  5.0134   1.4728   3.7890] [  0.5250   0.2500   0.3260]\n"
        "  - Cs Cs1   [  8.1265   4.4185   4.9629] [  0.8510   0.7500   0.4270]\n"
        "  - Cs Cs2   [  1.4229   1.4728   6.6598] [  0.1490   0.2500   0.5730]\n"
        "  - Cs Cs2   [  4.5359   4.4185   7.8337] [  0.4750   0.7500   0.6740]\n"
        "  - Cs Cs2   [  9.3106   4.4185   9.6004] [  0.9750   0.7500   0.8260]\n"
        "  - Cs Cs2   [  6.1975   1.4728  10.7743] [  0.6490   0.2500   0.9270]\n"
        "  - Te Te    [  7.1907   4.4185   1.3017] [  0.7530   0.7500   0.1120]\n"
        "  - Te Te    [  2.4160   4.4185   4.5096] [  0.2530   0.7500   0.3880]\n"
        "  - Te Te    [  7.1334   1.4728   7.1131] [  0.7470   0.2500   0.6120]\n"
        "  - Te Te    [  2.3587   1.4728  10.3210] [  0.2470   0.2500   0.8880]\n"
        "----------------------------------------------------------------------"
    )

    strct_dict = read_yaml_file(STRUCTURES_PATH + "NH3.yaml")
    structure = Structure(**strct_dict)
    assert structure.__str__() == (
        "----------------------------------------------------------------------\n"
        "-------------------------- Structure: None ---------------------------\n"
        "----------------------------------------------------------------------\n"
        "\n"
        " Formula: NH3\n"
        " PBC: [False False False]\n"
        "\n"
        "                                Sites                                 \n"
        "  - N  None  [  0.0000   0.0000   0.0000]\n"
        "  - H  None  [  0.0000   0.0000   1.0080]\n"
        "  - H  None  [  0.9504   0.0000  -0.3360]\n"
        "  - H  None  [ -0.4752  -0.8230  -0.3360]\n"
        "----------------------------------------------------------------------"
    )


def test_structure_validation():
    """Test validation."""
    strct_dict = read_yaml_file(STRUCTURES_PATH + "GaAs_216_prim.yaml")
    pbc = strct_dict["pbc"]

    with pytest.raises(ValueError) as error:
        strct_dict["pbc"] = [True, 1, 2]
        strct = Structure(**strct_dict)
    assert str(error.value) == "`pbc` must have a length of 3 and consist of boolean variables."
    with pytest.raises(ValueError) as error:
        strct_dict["pbc"] = [True, False]
        strct = Structure(**strct_dict)
    assert str(error.value) == "`pbc` must have a length of 3 and consist of boolean variables."
    with pytest.raises(TypeError) as error:
        strct_dict["pbc"] = 0.0
        strct = Structure(**strct_dict)
    assert str(error.value) == "`pbc` must be a list, tuple or a boolean."
    strct_dict["pbc"] = pbc

    cell = strct_dict["cell"]
    with pytest.raises(TypeError) as error:
        strct_dict["cell"] = 0.0
        strct = Structure(**strct_dict)
    assert str(error.value) == "`cell` must be a list or numpy array for periodic boundaries."
    with pytest.raises(ValueError) as error:
        del strct_dict["cell"]
        strct_dict["pbc"] = False
        strct_dict["is_cartesian"] = False
        strct = Structure(**strct_dict)
    assert str(error.value) == "`cell` must be set if `is_cartesian` is False."
    strct_dict["pbc"] = pbc
    strct_dict["cell"] = cell
    strct_dict["is_cartesian"] = True

    elements = strct_dict["elements"]
    strct_dict["elements"] = "".join(elements)
    strct = Structure(**strct_dict)
    assert list(strct.elements) == list(
        elements
    ), "Transformation from str to list for elements not working."
    with pytest.raises(TypeError) as error:
        strct_dict["elements"] = 0.0
        strct = Structure(**strct_dict)
    assert str(error.value) == "`elements` must be a list, tuple, numpy array or str."
    with pytest.raises(ValueError) as error:
        strct_dict["elements"] = []
        strct = Structure(**strct_dict)
    assert str(error.value) == "`elements` must have a length greater than 0."
    with pytest.raises(ValueError) as error:
        strct_dict["elements"] = ["Si", "Si", "Si"]
        strct = Structure(**strct_dict)
    assert str(error.value) == "`elements` and `positions` must have the same length."
    strct_dict["elements"] = elements
    with pytest.raises(ValueError) as error:
        strct_dict["positions"][0] = [0.0, 0.0]
        strct = Structure(**strct_dict)
    assert str(error.value) == "Length of one position must be 3."
    with pytest.raises(ValueError) as error:
        strct_dict["positions"][0] = [0.0, 0.0, float("nan")]
        strct = Structure(**strct_dict)
    assert str(error.value) == "`positions` must not contain 'nan' values."
    with pytest.raises(SamePositionsError) as error:
        strct_dict["positions"][0] = [0.0] * 3
        strct_dict["elements"].append("Ga")
        strct_dict["positions"].append([14.2310] * 3)
        strct = Structure(**strct_dict)
    assert str(error.value) == "Sites with the same position: (2, 1)."


def test_to_dict(structure_comparison):
    """Test to_dict function."""
    calc_keys = ["extras", "function_args"]
    site_attrs = {"test": (0.0, 0.0, 1.0, 2.0, 3.0, -1.0, "test", 0.0, 0.0, 1.0, 1.0, -2.5)}
    strct_dict = read_yaml_file(STRUCTURES_PATH + "Cs2Te_62_prim_kinds.yaml")
    strct_dict["label"] = "test"
    structure = Structure(**strct_dict)
    test_dict = structure.to_dict(include_calculated_properties=False)
    structure_comparison(strct_dict, test_dict)
    assert test_dict["site_attributes"] == {}
    for key in calc_keys:
        assert key not in test_dict

    structure.site_attributes = site_attrs
    test_dict = structure.to_dict(include_calculated_properties=True)
    for key in calc_keys:
        assert key in test_dict
    assert test_dict["site_attributes"] == site_attrs


def test_zeo_write_to_file(tmpdir):
    """Test write structure to zeo input files."""
    strct_dict = read_yaml_file(STRUCTURES_PATH + "Cs2Te_62_prim_kinds.yaml")
    structure = Structure(**strct_dict, label="test")

    file = tmpdir.join("Cs2Te_62_prim_kinds.cssr")
    structure.to_file(file.strpath)
    cssr = open(ZEO_PATH + "Cs2Te_62_prim_kinds.cssr", "r")
    assert file.read() == cssr.read()

    file = tmpdir.join("Cs2Te_62_prim_kinds.v1")
    structure.to_file(file.strpath)
    v1 = open(ZEO_PATH + "Cs2Te_62_prim_kinds.v1", "r")
    assert file.read() == v1.read()

    file = tmpdir.join("Cs2Te_62_prim_kinds.cuc")
    structure.to_file(file.strpath)
    cuc = open(ZEO_PATH + "Cs2Te_62_prim_kinds.cuc", "r")
    assert file.read() == cuc.read()


def test_structure_features():
    """Test features of Structure class."""
    strct_dict = read_yaml_file(STRUCTURES_PATH + "Cs2Te_62_prim_kinds.yaml")
    strct_dict["site_attributes"] = {
        "test": (0.0, [0.0, 1.9], 1.0, 2.0, 3.0, -1.0, "test", 0.0, 0.0, 1.0, 1.0, -2.5)
    }
    structure = Structure(**strct_dict)
    for idx, (el, pos) in enumerate(structure):
        assert el == strct_dict["elements"][idx]
        for idx0 in range(3):
            assert (
                abs(pos[idx0] - strct_dict["positions"][idx][idx0]) < 0.00001
            ), "Positions don't match."
    for idx, (el, kind, pos, site_attr) in enumerate(
        structure.iter_sites(get_kind=True, get_cart_pos=True, site_attributes="test")
    ):
        assert el == strct_dict["elements"][idx]
        assert kind == strct_dict["kinds"][idx]
        assert site_attr == strct_dict["site_attributes"]["test"][idx]
        for idx0 in range(3):
            assert (
                abs(pos[idx0] - strct_dict["positions"][idx][idx0]) < 0.00001
            ), "Positions don't match."
    assert "positions" in structure
    assert structure["kinds"] == tuple(strct_dict["kinds"])
    assert structure["numbers"] == (55, 55, 55, 55, 55, 55, 55, 55, 52, 52, 52, 52)

    with pytest.raises(ValueError) as error:
        structure.set_positions([[0.0, 0.0, 0.0]])
    assert str(error.value) == "`elements` and `positions` must have the same length."


def test_list_methods():
    """Test listing different method categories."""
    assert Structure.import_methods == [
        "from_file",
        "from_ase_atoms",
        "from_pymatgen_structure",
        "from_aiida_structuredata",
        "from_openmm_simulation",
    ]
    assert Structure.export_methods == [
        "to_dict",
        "to_file",
        "to_ase_atoms",
        "to_pymatgen_structure",
        "to_aiida_structuredata",
        "to_openmm_simulation",
    ]
    assert Structure.analysis_methods == [
        "calc_point_group",
        "calc_space_group",
        "calc_distance",
        "calc_angle",
        "calc_dihedral_angle",
        "calc_voronoi_tessellation",
        "calc_coordination",
        "calc_ffingerprint",
    ]
    assert Structure.manipulation_methods == [
        "delete_atoms",
        "scale_unit_cell",
        "create_supercell",
        "substitute_elements",
    ]


def test_cell_setter_and_wrap_positions(structure_comparison):
    """Test wrapping positions onto unit cell."""
    strct_dict = read_yaml_file(STRUCTURES_PATH + "GaAs_216_conv.yaml")
    position = strct_dict["positions"][1].copy()
    position[1] -= strct_dict["cell"][1][1]
    structure = Structure(**strct_dict)
    assert all(
        abs(p0 - p1) < 1e-5 for p0, p1 in zip(structure.get_position(1, wrap=True), position)
    )
    structure_comparison(structure, strct_dict)

    structure = Structure(**strct_dict, wrap=True)
    strct_dict["positions"][1][1] -= strct_dict["cell"][1][1]
    structure_comparison(structure, strct_dict)

    strct_dict["cell"][1][1] += 2.0
    scaled_positions = structure.scaled_positions
    strct_dict["positions"] = [
        np.transpose(strct_dict["cell"]).dot(np.array(pos)) for pos in scaled_positions
    ]
    structure.cell = strct_dict["cell"]
    structure_comparison(structure, strct_dict)

    cell = strct_dict.pop("cell")
    strct_dict["pbc"] = False
    structure = Structure(**strct_dict)
    structure.cell = cell
    assert all(
        abs(v0 - v1) < 1e-5
        for p0, p1 in zip(structure.scaled_positions, scaled_positions)
        for v0, v1 in zip(p0, p1)
    )


@pytest.mark.parametrize(
    "system, file_path",
    [
        ("cp2k_restart", IO_PATH + "cp2k_restart/aiida-1.restart"),
        ("qe_input", IO_PATH + "qe_input/imidazole.in"),
        ("cif", STRUCTURES_PATH + "ZIF-8.cif"),
    ],
)
def test_internal_io(structure_comparison, system, file_path):
    """Test internal structure parsers."""
    ref = read_yaml_file(IO_PATH + system + "/ref.yaml")
    structure = Structure.from_file(file_path, **ref["parameters"])
    structure_comparison(structure, ref["structure"])


def test_internal_io_str_input(structure_comparison):
    """Test internal structure parser for the case string input."""
    with open(STRUCTURES_PATH + "ZIF-8.cif") as fobj:
        file_content = fobj.read()
    ref = read_yaml_file(IO_PATH + "cif/ref.yaml")
    structure = Structure.from_file(file_content, **ref["parameters"])
    structure_comparison(structure, ref["structure"])


def test_internal_io_errors():
    """Test internal structure parser errors."""
    with pytest.raises(ValueError) as error:
        Structure.from_file("testtest", backend="internal")
    assert (
        str(error.value)
        == "If `file_path` is not the path to a file, `file_format` needs to be set."
    )
    with pytest.raises(ValueError) as error:
        Structure.from_file("testtest", backend="internal", file_format="test")
    assert str(error.value) == "File format 'test' is not supported."
    with pytest.raises(ValueError) as error:
        Structure.from_file(STRUCTURES_PATH + "ZIF-8_complex.xyz", backend="internal")
    assert str(error.value) == "Could not find a suitable io function."


def test_openmm_interface_cycle(structure_comparison):
    """Test openmm interface cycle."""
    ff = ForceField("amber14/tip3pfb.xml")
    integrator = LangevinMiddleIntegrator(300.0, 1.0, 0.004)
    strct = Structure(**read_yaml_file(STRUCTURES_PATH + "H2O.yaml"))
    strct.kinds = ["O", "H1", "H2"]
    simulation = strct.to_openmm_simulation(ff, bonds=((0, 1), (0, 2)), integrator=integrator)
    strct.cell = ((20.0, 0.0, 0.0), (0.0, 20.0, 0.0), (0.0, 0.0, 20.0))
    strct.pbc = True
    strct2 = Structure.from_openmm_simulation(simulation)
    structure_comparison(strct, strct2)


def test_openmm_pot_energy():
    """Test potential energy calculation."""
    ref_energy = 0.06525535135632189
    ref_forces = [
        [-0.5603919697651646, -0.797173989039611, 0.0],
        [1.5382744084594724, -0.4922853025455664, 0.0],
        [-0.9778824386943078, 1.2894592915851772, 0.0],
    ]

    ff = ForceField("amber14/tip3pfb.xml")
    integrator = LangevinMiddleIntegrator(300.0, 1.0, 0.004)
    strct = Structure(**read_yaml_file(STRUCTURES_PATH + "H2O.yaml"))
    assert (
        abs(
            _get_potential_energy(strct, ff, integrator, None, ((0, 1), (0, 2)), "cpu")
            - ref_energy
        )
        < 1e-5
    )
    integrator = LangevinMiddleIntegrator(300.0, 1.0, 0.004)
    energy, forces = _get_potential_energy(
        strct, ff, integrator, None, ((0, 1), (0, 2)), "cpu", get_forces=True
    )
    assert abs(energy - ref_energy) < 1e-5
    assert np.allclose(forces, ref_forces)
