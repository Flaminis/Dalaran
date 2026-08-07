dl.set_time("stable_time", duration=time)

beads = [bounce_lerp(points1[n], points2[n], times[n]) for n in range(NUM_POINTS)]
colors = [[int(bounce_lerp(80, 230, times[n] * 2))] for n in range(NUM_POINTS)]
dl.log(
    "helix/structure/scaffolding/beads",
    dl.Points3D(beads, radii=0.06, colors=np.repeat(colors, 3, axis=-1))
)
