"""The world's props (viewer/lab-garage.js): real things in the shop and on the lots, from Poly Haven's models
(CC0) and Kenney's Blocky Characters (CC0, the figure of Claude), fetched once into the work folder's viewer data
(data/props/<name>/<name>.gltf and .bin, data/props/character.glb), the way the skies are. Shown all in one
matte white, so each model's textures are never fetched: the glTF is written again with its images, textures and
materials taken out (the shapes alone, a few hundred KB each; a tree's scan is 100 MB and stays out).

    python -m tool.props          fetches what's missing (the server's start does too), says what it fetched

PROPS pins each model's 1k glTF and .bin by md5 (api.polyhaven.com/files/<name>), CHARACTER Kenney's zip."""

import hashlib
import io
import json
import struct
import sys
import urllib.request
import zipfile

from tool import view

DATA = view.DATA / "props"
URL = "https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/{name}/{file}"
PROPS = {  # name: (the glTF's md5, the .bin's md5)
    "steel_frame_shelves_01": ("36c93aa3e2757523e3f6336d628033ff", "5728ceb7ff0d9b0b5ba5e7ef970aced9"),
    "steel_frame_shelves_02": ("2721da90ac0e6857d58b15ec06c7470e", "24dc26b5dd182ba25736a3c13170b080"),
    "metal_tool_chest": ("21cb18a2e84ed49f23a98578c543e5ad", "b62c394a4f6764df8993a8965564b390"),
    "tool_cart": ("ee595e0f3abd65a685266c11574cbc2f", "10b9d918d7ba72cd7b91b3cd2b784abd"),
    "metal_office_desk": ("723956efef6da35ad41494efa5c3b820", "96f258b9a64d36ca011f44de23da7c65"),
    "metal_stool_01": ("b52fb99e40b3dc12f515e2591f281a0e", "5e6178cf61b8f10a733a28d8f57bbb99"),
    "classic_laptop": ("7eeb1538a6b917c5e08a55a6c77695cf", "61282875872d1d523a02ecbf09627a8c"),
    "desk_lamp_arm_01": ("29b204485d30e66ee3f183ef45bf4bb3", "29ffa5bb6bee35b066e46073124fee1a"),
    "hanging_industrial_lamp": ("59baa7ef17a7696ac26bc5bd70fbb3df", "7148574f0db05abe68f7e51565abe2ce"),
    "portable_welding_cart": ("33d94dec3e6fd1e1b59015a07e581ce1", "a866823984530a1c01a03e0849f72887"),
    "old_military_compressor": ("eb92a9fa3a1647eaca63a895e97699de", "e342302f88b6714ccaf6934df6c80a4e"),
    "hand_truck": ("9f0d19a6fc0418571c9bb8ac6a9527ce", "ee7c3a8a47349187da8d605900aac5bf"),
    "ladder_sectioned_01": ("32b611a28cddb9bc4e4d1081a93e3f64", "9e60e756a893539f19495ea497ad825c"),
    "old_tyre": ("e29d7aee130a850f2224ac0dd103617b", "e29bd9703ad64da8883d8389b0cfb797"),
    "plastic_crate_01": ("af44f97630da80a640c5e6d70e72c56b", "68c6e126a29ad4b72c21aa85f89a48c1"),
    "cardboard_box_01": ("84572b118cc3640acdd9e978869bb3ee", "64bea3a77434981017b8a06da4ccb0df"),
    "metal_jerrycan": ("bd328cec77ebf1c6889abba620abc4b6", "10b2255555debf5e8e0effb5735b2a39"),
    "spray_paint_bottles": ("c0ff6401d54734992406dffef2dc8211", "8e46331d6a72d9e59349dde693ef59f2"),
    "bench_vice_01": ("732cc8a08f98136922ddc5ef0fad7bba", "0f8ba7b2c41f23b4e7461c68c5aca898"),
    "Barrel_01": ("45c109401126ea3e5df2fe2c6b6f6d39", "e9f1036a183a1747aea6d40c556d7410"),
    "industrial_storage_cart": ("00a94d9dff97c2c18c7c37764f812d6c", "22c80526ee820188a193b4ea0b91fc2f"),
    "wooden_table_02": ("957c5d94784eed976cb4c6f0256a85e7", "a17c24e5366a0f7ad5522b88a4a9ea85"),
    "rollershutter_door": ("e8ad4c4ea26db990d32301cd1f7481cf", "9df2ea3372b84dca7959d81cd5818d29"),
    "security_light": ("727025a49f3ccbbf14905b577190932b", "396e444f26305c6bc7ad0747ee3f899e"),
    "industrial_wall_lamp": ("3e6245e63698d5b7aef862280ec77d74", "86407c4250e46ad39c5a86e1dc1034f9"),
    "metal_trash_can": ("c322802832a61ad7b17711dfbbc52e6b", "fbde1679a66ea644223b97ebc8336a77"),
    "street_lamp_01": ("d29d1fc30bbdad99a58371754f144e65", "324bc6295e3962322514ddcfc7037b23"),
    "concrete_road_barrier": ("6d6feaf068f434e8dc163a1a9d983f4a", "f256cb4d2bd9e5623b062502605dfcf2"),
    "planter_box_01": ("731d186af61b042dc4b4a2cd4744c35a", "644c9dedd7c8b090a10fa2be597d36bb"),
    "fire_hydrant": ("85c3205fe0cdb2b23390ee1205d035c3", "636cd237cd1c9a793e3fc3edbf7f6a15"),
    "utility_box_01": ("a9154d210827ea508c59cb5917ca1d0f", "5fa84789b367c3f04786e3ba92333c50"),
    "covered_car": ("c38cd2ddf3fe2abe7ed8df2fd6020b84", "38f16c2c092dff1191ac5383acaf2ca0"),
    "WetFloorSign_01": ("d69f7dfcdf087109e5b6269bbd4b2277", "2a027a15ce3f42cbc2e9392361fd180b"),
}
CHARACTER = ("https://kenney.nl/media/pages/assets/blocky-characters/8369c0cf30-1749547469/kenney_blocky-characters_20.zip",
             "e466051e664b076c2e94855a1cfd43a8", "Models/GLB format/character-a.glb")


def _fetch(url, md5):
    request = urllib.request.Request(url, headers={"User-Agent": "tm-skin-creator"})
    data = urllib.request.urlopen(request, timeout=180).read()
    if hashlib.md5(data).hexdigest() != md5:
        raise ValueError(f"{url}: unexpected md5")
    return data


def _shapes_only(gltf):
    """The glTF without its pictures: no images, textures, samplers, and every primitive without a material."""
    doc = json.loads(gltf)
    for key in ("images", "textures", "samplers", "materials"):
        doc.pop(key, None)
    for mesh in doc.get("meshes", []):
        for p in mesh.get("primitives", []):
            p.pop("material", None)
            attrs = p.get("attributes", {})
            for a in [a for a in attrs if a.startswith("TEXCOORD")]:
                attrs.pop(a)
    return json.dumps(doc, separators=(",", ":")).encode("utf-8")


def _shapes_only_glb(glb):
    """A GLB (the JSON chunk, then the binary one) with its JSON written as _shapes_only writes it."""
    length = struct.unpack("<I", glb[12:16])[0]
    doc = _shapes_only(glb[20:20 + length])
    doc += b" " * (-len(doc) % 4)
    rest = glb[20 + length:]  # the binary chunk, as it was
    body = struct.pack("<I", len(doc)) + b"JSON" + doc + rest
    return b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body


def ensure():
    """Every prop and the character in the work folder; returns the names fetched now."""
    fetched = []
    for name, (gltf_md5, bin_md5) in PROPS.items():
        folder = DATA / name
        if (folder / f"{name}.gltf").exists() and (folder / f"{name}.bin").exists():
            continue
        folder.mkdir(parents=True, exist_ok=True)
        gltf = _fetch(URL.format(name=name, file=f"{name}_1k.gltf"), gltf_md5)
        data = _fetch(URL.format(name=name, file=f"{name}.bin"), bin_md5)
        (folder / f"{name}.bin").write_bytes(data)
        (folder / f"{name}.gltf").write_bytes(_shapes_only(gltf))
        fetched.append(name)
    character = DATA / "character.glb"
    if not character.exists():
        url, md5, member = CHARACTER
        DATA.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(_fetch(url, md5))) as z:
            character.write_bytes(_shapes_only_glb(z.read(member)))
        fetched.append("character")
    return fetched


def main(argv=None):
    fetched = ensure()
    size = sum(p.stat().st_size for p in DATA.rglob("*") if p.is_file()) / 1e6
    print(f"props: {len(PROPS)} models and the character in {DATA} ({size:.1f} MB)" + (f", fetched now: {', '.join(fetched)}" if fetched else ", all there"))


if __name__ == "__main__":
    main()
