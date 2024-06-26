!-----------------------BEGIN NOTICE -- DO NOT EDIT-----------------------
! NASA Goddard Space Flight Center
! Land Information System Framework (LISF)
! Version 7.5
!
! Copyright (c) 2024 United States Government as represented by the
! Administrator of the National Aeronautics and Space Administration.
! All Rights Reserved.
!-------------------------END NOTICE -- DO NOT EDIT-----------------------
!BOP
! 
! !ROUTINE: neighbor_interp
!  \label{neighbor_interp}
!
! !INTERFACE:
subroutine neighbor_interp(gridDesco,li,gi,lo,go,mi,mo, & 
     rlat,rlon,n11,udef, iret)
  implicit none
! 
! !USES:   
!
! !INPUT PARAMETERS: 
! 
! !OUTPUT PARAMETERS:
!
! !DESCRIPTION: 
! !DESCRIPTION: 
!  This subprogram performs neighbor search interpolation
!  from any grid to any grid for scalar fields. The routine is based
!  on the spatial interpolation package ipolates from NCEP. 
!             
!  The algorithm simply performs a nearest neighbor search 
!  around each output grid point for interpolation. 
!  The grids are defined by their grid description arrays. 
!  
!  The grid description arrays are based on the decoding 
!  schemes used by NCEP. However, in order to remove the integer
!  arithmetic employed in the original ipolates, the routines
!  are rewritten using real number manipulations. The general 
!  structure remains the same. 
!    
!  The current code recognizes the following projections: \newline
!             (gridDesc(1)=0) equidistant cylindrical \newline
!             (gridDesc(1)=1) mercator cylindrical \newline
!             (gridDesc(1)=3) lambert conformal conical \newline
!             (gridDesc(1)=4) gaussian cylindrical (spectral native) \newline
!             (gridDesc(1)=5) polar stereographic azimuthal \newline
!  where gridDesc could be defined for either the input grid or the 
!  output grid. The routine also returns the  
!  the number of output grid points
!  and their latitudes and longitudes are also returned.
!  The input bitmaps will be interpolated to output bitmaps.
!  output bitmaps will also be created when the output grid
!  extends outside of the domain of the input grid.
!  the output field is set to 0 where the output bitmap is off.
! 
!  The arguments are: 
!  \begin{description}
!    \item[gridDesco]
!     output grid description parameters 
!    \item[ibi] 
!     integer input bitmap flags
!    \item[li]
!     logical input bitmaps
!    \item[gi]
!     real input fields to interpolate
!    \item[ibo]
!     integer output bitmap flags
!    \item[lo]
!     logical output bitmaps
!    \item[go]
!     real output fields interpolated
!    \item[mi]
!     integer dimension of input grid fields 
!    \item[mo]
!     integer dimension of output grid fields
!    \item[rlat]    
!     output latitudes in degrees
!    \item[rlon]    
!     output longitudes in degrees
!    \item[n11]    
!     index of neighbor points
!    \item[udef]
!     undefined value to be used
!    \item[iret]
!     return code (0-success)
!    \end{description}
!
!  The routines invoked are: 
!  \begin{description}
!   \item[polfixs](\ref{polfixs}) \newline
!    Apply corrections for poles
!  \end{description}
! 
! !FILES USED:
!
! !REVISION HISTORY:
!   04-10-96  Mark Iredell; Initial Specification
!   05-27-04  Sujay Kumar : Modified verision with floating point arithmetic, 
! 
!EOP
!BOP
! 
! !ARGUMENTS: 
  real      :: gridDesco(50)
  integer   :: mi
  integer   :: mo
  logical*1 :: li(mi)
  logical*1 :: lo(mo)
  real      :: gi(mi)
  real      :: go(mo)
  real      :: rlat(mo)
  real      :: rlon(mo)
  integer   :: n11(mo)
  real      :: udef
  integer   :: iret
!
!EOP
  integer   :: ibi
  integer   :: ibo
  integer :: nn
  integer n
  
  real, parameter :: fill=-9999.
  nn = mo
  ibi = 1
! - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
!  INTERPOLATE WITH OR WITHOUT BITMAPS
  lo = .false.

  do n=1, nn
     go(n)=0.
     if(n11(n).gt.0) then
        if(ibi.eq.0.or.li(n11(n))) then 
           go(n) = gi(n11(n))
           lo(n) = .true.
        endif 
     endif
  enddo
  ibo = ibi
  do n=1,nn
     if(.not.lo(n)) then 
        ibo = 1
        go(n) = udef
     endif
  enddo
  if(gridDesco(1).eq.0) call polfixs(nn,mo,1,rlat,rlon,ibo,lo,go)
  iret = 0 
end subroutine neighbor_interp
