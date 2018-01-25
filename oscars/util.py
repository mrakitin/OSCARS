import os
import copy
import numpy as np
import uuid
import oscars.sr

def read_file_list(ifile, idir=None):
    """
    read a list of parameters and filenames from a file.
    
    The file format should be two columns separated by whitespace.
    In the first column is the parameter value as a floating point number
    and in the second column the file name.  Whitespace in the name is
    unforgivably wrong, but technically allowed.
    
    Parameters
    ----------
    ifile : str
        Full path to file containing the list of parameters and filenames
        
    idir : str
        Path to directory where the files are contained if not in the 'ifile' directory
        
    Returns
    -------
    file_list : list
        List of [parameter, filename]s
    """
    
    # Directory where files are
    mydir = os.path.dirname(ifile)
    if idir is not None:
        mydir = idir
    
    # List we will return
    mylist=[]
    with open(ifile, 'r') as fi:
        for l in fi:
            ls = l.split()
            pv = float(ls[0])
            fn = os.path.join(mydir, ' '.join(ls[1:]))
            
            mylist.append([pv, fn])
            
    return mylist





def read_file_list2(ifile, gap=None, phase_mode=None, phase=None, idir=None):
    """
    read a list of parameters and filenames from a file.
    
    The file format should be four columns separated by whitespace.
    The columns are gap value, phase mode, phase value, file name.
    Whitespace in the phase mode is not allowed.

    One can specify the following:
        gap + phase_mode
        phase + phase_mode
    
    Parameters
    ----------
    ifile : str
        Full path to file containing the list of parameters and filenames

    gap : float
        Gap value of interest (must be exact match, not interpolated)

    phase_mode : str
        Phase mode of interest

    phase : float
        Phase value
        
    idir : str
        Path to directory where the files are contained if not in the 'ifile' directory
        
    Returns
    -------
    file_list : list
        List of [gap, phase_mode, phase, filename]s
    """
    
    # Directory where files are
    mydir = os.path.dirname(ifile)
    if idir is not None:
        mydir = idir
    
    print(mydir)
    # List we will return
    mylist=[]
    with open(ifile, 'r') as fi:
        for l in fi:
            ls = l.split()
            if len(ls) < 4:
                continue
                
            g  = float(ls[0])
            pm = ls[1]
            ph = float(ls[2])
            fn = os.path.join(mydir, ' '.join(ls[3:]))
     
            if phase_mode is None and phase is None and gap == None:
                mylist.append([g, pm, ph, fn])
            elif gap is not None and phase_mode is not None:
                if g == gap and phase_mode == pm:
                    mylist.append([ph, fn])
            elif phase is not None and phase_mode is not None:
                if phase == ph and phase_mode == pm:
                    mylist.append([g, fn])
            
    return mylist







def read_file_list_interpolate_2d(ifile, iformat, gap=None, phase_mode=None, phase=None, idir=None, tmpdir=None, ofile=None):
    """
    read a list of parameters and filenames from a file.  Interpolate across phases for each gap to get
    desired phase at each gap, then Interpolate across gaps to arrive at gap and phase, for a given mode
    
    The file format should be four columns separated by whitespace.
    The columns are gap value, phase mode, phase value, file name.
    Whitespace in the phase mode is not allowed.

    One must specify: gap, phase, phase_mode
    
    Parameters
    ----------
    ifile : str
        Full path to file containing the list of parameters and filenames

    gap : float
        Gap value of interest (must be exact match, not interpolated)

    phase_mode : str
        Phase mode of interest

    phase : float
        Phase value
        
    idir : str
        Path to directory where the files are contained if not in the 'ifile' directory
        
    Returns
    -------
    file_list : list
        List of [gap, phase_mode, phase, filename]s
    """

    if ofile is None:
        raise ValueError('Must specify output file as ofile')

    # Set temporary directory for interpolating results
    if tmpdir is None:
        tmpdir = '.OSCARS_tmp_' + str(uuid.uuid4())

    if os.path.exists(tmpdir):
        raise

    os.makedirs(tmpdir)
    
    # Directory where files are
    mydir = os.path.dirname(ifile)
    if idir is not None:
        mydir = idir

    # oscars.sr object for interpolation
    osr = oscars.sr.sr(gpu=0, nthreads=1)

    # Store all phases that a gap has
    phases_at_gap = dict()
    
    #print(mydir)
    # List we will return
    mylist=[]
    with open(ifile, 'r') as fi:
        for l in fi:
            ls = l.split()
            if len(ls) < 4:
                continue
            if ls[0].lstrip()[0] == '#':
                continue
                
            g  = float(ls[0])
            pm = ls[1]
            ph = float(ls[2])
            fn = os.path.join(mydir, ' '.join(ls[3:]))
     
            if pm != phase_mode:
                continue

            if g in phases_at_gap:
               phases_at_gap[g].append([ph, fn])
            else:
                phases_at_gap[g] = [[ph, fn]]

    new_mapping = []

    for key in phases_at_gap:
        #print(key)
        #for asd in phases_at_gap[key]:
        #    print(asd)
        tmp_file_name = tmpdir + '/gap' + str(key) + '.dat'
        new_mapping.append([key, tmp_file_name])

        osr.clear_bfields()
        osr.add_bfield_interpolated(mapping=phases_at_gap[key], iformat=iformat, parameter=phase, ofile=tmp_file_name)

    osr.clear_bfields()
    osr.add_bfield_interpolated(mapping=new_mapping, iformat=iformat, parameter=gap, ofile=ofile)

    for pair in new_mapping:
        os.remove(pair[1])

    os.rmdir(tmpdir)
            
    return ofile





def scale_spectrum(s, c):
    """Multiple spectrum by constant c"""
    
    for l in s:
        l[1] *= c
        
    return

def add_spectra(spectra):
    """Add spectra from list spectra and return new spectrum"""
    
    spectrum=copy.deepcopy(spectra[0])

    N = len(spectrum)

    for isp in range(1, len(spectra)):
        if len(spectra[isp]) != N:
            raise ValueError('spectra do not have the same dimensions')
        for i in range(len(spectra[isp])):
            spectrum[i][1] += spectra[isp][i][1]
        
    return spectrum



def add_flux(f):
    """Add flux from list of fluxes and return new summed flux"""
    
    fsummed = copy.deepcopy(f[0])

    N = len(fsummed)

    for ifn in range(1, len(f)):
        if len(f[ifn]) != N:
            raise ValueError('flux do not have the same dimensions')

        for i in range(len(f[ifn])):
            fsummed[i][1] += f[ifn][i][1]
        
    return fsummed



def add_power_density(p):
    """Add power densities from list of power densities and return new summed power density"""
    
    return add_flux(p)



def rebin (H, ANX=2, ANY=2):
    """rebin 2d histogram"""
    
    NX = len(np.unique([h[0][0] for h in H]))
    NY = len(np.unique([h[0][1] for h in H]))
    print(NX, NY)
    HNEW = []

    i=0
    while i < NX:
        j=0
        while j < NY:
            x = H[i*NY + j][0][0]
            y = H[i*NY + j][0][1]
            f = 0
            count = 0
            for m in range(ANX):
                if i + m >= NX:
                    continue
                for n in range(ANY):
                    if j + n >= NY:
                        continue
                    count += 1
                    f += H[(i+m)*NY + j+n][1]
                    
            f /= (count)
            HNEW.append([[x, y, 0], f])
            j+=ANY
            #print(x, y, f)
            
        i+=ANX
     
    
    return HNEW
