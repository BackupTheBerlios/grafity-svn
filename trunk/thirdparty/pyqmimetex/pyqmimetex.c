#include <stdio.h>
#include <stdlib.h>
#include "mimetex.h"
#include "pyqmimetex.h"

/* --- global needed by callback function, below, for gifsave.c --- */
static raster *rp = NULL;	/* 0/1 bitmap raster image */

/* ---  callback function to return pixel value at col x, row y --- */
int Getpixel(int x, int y)
{				/* pixel value will be 0 or 1 */
	return (int) getpixel(rp, y, x);
}				/* just use getpixel() macro */

/* --- main() entry point --- */
int mimetex_main(char *expression, char *filename)
{
	/* ---- mimeTeX converts expression to bitmap raster ---- */
	rp = make_raster(expression, NORMALSIZE);	/* mimeTeX rasterizes expression */
	/* ---- convert returned bitmap raster to gif, and emit it on stdout ---- */
	/* --- initialize gifsave library and colors, and set transparent bg --- */
	GIF_Create(filename, rp->width, rp->height, 2, 8);	/* init for black/white */
	GIF_SetColor(0, 255, 255, 255);	/* always set background white */
	GIF_SetColor(1, 0, 0, 0);	/* and foreground black */
	GIF_SetTransparent(0);	/* and set transparent background */
	/* --- finally, emit compressed gif image (to stdout) --- */
	GIF_CompressImage(0, 0, -1, -1, Getpixel);
	GIF_Close();
}

PyObject *mimetex_data(PyObject *self, PyObject *args)
{
	char *expression;
    char *filename = tempnam(NULL, NULL);

	if (!PyArg_ParseTuple(args, "s", &expression)) {
		return NULL;
	}

    mimetex_main(expression, filename);
	return Py_BuildValue("s", filename);
}

static char mimetex__doc__[] =
    "odr(fcn, beta0, y, x,\nwe=None, wd=None, fjacb=None, fjacd=None,\nextra_args=None, ifixx=None, ifixb=None, job=0, iprint=0,\nerrfile=None, rptfile=None, ndigit=0,\ntaufac=0.0, sstol=-1.0, partol=-1.0,\nmaxit=-1, stpb=None, stpd=None,\nsclb=None, scld=None, work=None, iwork=None,\nfull_output=0)";

static PyMethodDef methods[] = {
	{"mimetex_data", (PyCFunction) mimetex_data,
	 METH_VARARGS | METH_KEYWORDS, mimetex__doc__},
	{NULL, NULL},
};

void init__mimetex()
{
	Py_InitModule("__mimetex", methods);
}
