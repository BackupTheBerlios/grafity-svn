all: grafit.msi

grafit.msi: grafit.wixobj data.wixobj
	light -out grafit.msi grafit.wixobj data.wixobj

grafit.wixobj: grafit.wxs
	candle grafit.wxs

data.wixobj: data.wxs
	candle data.wxs
