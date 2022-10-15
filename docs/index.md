# Curve Equalizer

Curve Equalizer helps you quickly balance the Bézier handles of a curve, or adjust the curvature to a chosen amount.

## Interface

<img src="dialog.png" width="234" height="158" alt="">

Select the curve adjustment method.

<table>
	<tr>
		<th>Method</th>
		<th>Description</th>
	</tr>
	<tr>
		<td>Circle</td>
		<td>The result is similar to what FontLab Studio 5 does when you alt-shift-click a curve segment. If the triangle between the first and last point of the segment is rectangular with two 45° angles, the result will approximate a quarter circle.</td>
	</tr>
	<tr>
		<td>Rule of thirds</td>
		<td>The resulting handles and an imaginary line between the two handles will each be nearly equal in length.</td>
	</tr>
	<!--<tr>
		<td>TT (experimental)</td>
				<td>Change the curve so it is well suited for conversion to a quadratic (TrueType) Bézier curve. Don’t use this, the results are terrible at the moment.</td>
	</tr>-->
	<tr>
		<td>Balance</td>
		<td>The curvature is not changed, only the length of the handles is distributed evenly between the in- and outgoing handle. This is similar to the «Tunnifier» script by Eduardo Tunni.</td>
	</tr>
	<tr>
		<td>Fixed</td>
		<td>Select the desired curvature from the horizontal radio buttons. The first will result in the same curve as the «Circle» method. The other buttons gradually add more curvature.</td>
	</tr>
	<tr>
		<td>Adjust</td>
		<td>Change the curvature interactively using the slider. This is particularly useful if you want to finely tweak the curvature, while balancing the handles.</td>
	</tr>
	<tr>
		<td>Hobby</td>
		<td>Change the tension of the curves. This uses the spline algorithm by John D. Hobby, which is also used by Metafont to create harmonic curves.</td>
	</tr>
</table>

Click the «Equalize selected» button to apply the adjustment to the selected curves in the current glyph window.

Tip: you can make the window larger, this will give you longer sliders and thus more precision.

## Known Issues

If the angle between the Bézier handles is less than 45°, or the handles are on different sides of the curve, the curvature can’t be changed. This is not a bug.

The modified curves preview is not visible while you hold the Preview keyboard shortcut.

## Geometry

These are my notes from which I derived the trigonometry at work:

<img src="geometry.jpg" width="370" height="305" alt="">

<hr>

Curve Equalizer is © 2013–2022 by Jens Kutilek.

The Hobby Spline code was sent in by Simon Egli with contributions by Juraj Sukop and Lasse Fister.
