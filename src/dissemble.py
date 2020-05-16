import pandas as pd
import numpy as np
from scipy.linalg import toeplitz
import scipy.linalg as linalg

from scipy.linalg import solve_triangular


# https://stackoverflow.com/questions/17869840/numpy-vector-n-1-dimension-n-dimension-conversion
# https://stackoverflow.com/questions/20231063/r-writing-an-array-to-a-file

# Writing a positive definite matrix

# https://stat.ethz.ch/pipermail/r-help/2008-February/153708

# Step 1 :For now, we will implement the CalcGLS function available below slowly
# https://rdrr.io/cran/tempdisagg/src/R/td.calc.R#sym-CalcGLS

# (a) get the same inputs from R => x, X, vcov # use rho = 0.5 to calculate vcov for now

y_l_data = pd.read_csv("C:/Users/jstep/Documents/y_l.csv")
X_data = pd.read_csv("C:/Users/jstep/Documents/X.csv")

y_l = np.asarray(y_l_data["V1"])
X = np.asarray(X_data["exports.q"])

# Set up CalcC
# inputs
n = len(X)
n_l = len(y_l)
conversion = "sum"
fr = 4 # ratio of high-freq to low-freq for eg, for quartertly to yearly it's 4
n_bc = 12 # number of back-casting periods, identified my mismatch of starting X and y
n_fc = 2 # number of fore-casting periods, identified my mismatch of ending X and y

# C <- CalcC(n_l = n_l,conversion = "sum",fr = 4,n.bc=12,n.fc=2)

# fr = 4
# n_l = 5

# if conversion == "sum":
conversion_weights = np.repeat(1, fr).reshape((1,4))

diagonal_identity = np.identity(n_l)
conversion_weights_T = conversion_weights.T
C = np.kron(diagonal_identity,conversion_weights_T).T

if n_fc > 0:
    C = np.hstack((C,np.zeros((C.shape[0], n_fc))))

if n_bc > 0:
    C = np.hstack((np.zeros((C.shape[0], n_bc)), C))

pm = np.array(toeplitz(np.arange(n)),dtype=np.float64)

X_l = C.dot(X.reshape(len(X),1))

# Calculate vcov first
# assume rho = 0.5

# vcov = C %*% CalcQ(rho, pm) %*% t(C)

rho = 0.5
# let
#pm = toeplitz(np.arange(3))

CalcQ = (1 / (1 - rho**2))*(rho**pm)

vcov = (C.dot(CalcQ)).dot(C.T)

# Now we implement CalcGLS. Buckle up!
# y = y_l
# X = X_l
# vcov = vcov

b = y_l
A = X_l
W = vcov

m = A.shape[0]
n = A.shape[1]

# B <- t(chol(W)) No need to transpose here apparently, let's see
B = np.linalg.cholesky(W)

# QR decomposition of X
Q, R = linalg.qr(X_l)

# R from QR factorization in python keeps all zeroes from the array
# Remove these zeroes to match R implementation

R = R[~np.all(R == 0, axis=1)]

# Application to b and B
# .c <- t(Q) %*% b
# c1 <- .c[1:n, ]
# c2 <- .c[(n + 1):m, ]

c_bB = Q.T.dot(b)
c_bB1 = c_bB[0:n]
c_bB2 = c_bB[n:m]

# Everything from down here will be parameterized by rho by sympy with god's help

# .C <- t(Q) %*% B
# C1 <- .C[1:n, ]
# C2 <- .C[(n + 1):m, ]

C_bB = Q.T.dot(B)
C_bB1 = C_bB[0:n]
C_bB2 = C_bB[n:m]

# tC2 <- t(C2)
# ftC2 <- tC2[dim(tC2)[1]:1, dim(tC2)[2]:1]

C_bB2_T = C_bB2.T
ft_C_bB2 = np.flip(C_bB2_T[0:C_bB2_T.shape[0],0:C_bB2_T.shape[1]])

# rq.ftC2 <- qr(ftC2)
# PP <- qr.Q(rq.ftC2, complete = TRUE)
# SS <- qr.R(rq.ftC2)

PP, SS = linalg.qr(ft_C_bB2)
SS = SS[~np.all(SS == 0, axis=1)]

# P <- PP[dim(PP)[1]:1, dim(PP)[2]:1]
# S <- t(SS[dim(SS)[1]:1, dim(SS)[2]:1])

P = np.flip(PP[0:PP.shape[0], 0:PP.shape[1]])
S = np.flip(SS[0:SS.shape[0], 0:SS.shape[1]]).T

P1 = P[:, 0:n]
P2 = P[:, n:m]

# u2 <- matrix(backsolve(S, c2))

u2 = solve_triangular(S,c_bB2)

v = P2.dot(u2)
v = v.reshape(len(v),1)

# x <- backsolve(R, c1 - C1 %*% v)
x = solve_triangular(R, c_bB1 - C_bB1.dot(v))

# z$rss <- as.numeric(t(u2) %*% u2)

z_rss = u2.T.dot(u2)

z_s_2 = z_rss/m

z_logl = -m/2 - m*np.log(2*3.14)/2 - m*np.log(z_s_2)/2 - np.log(np.linalg.det(vcov))/2


# z$logl <- as.numeric(-m / 2 - m * log(2 * pi) / 2 - m * log(z$s_2) /
#                        2 - log(det(vcov)) / 2)

# Objective <- function(rho) {
#   -CalcGLS(
#     y = y_l, X = X_l, vcov = C %*% CalcQ(rho, pm) %*% t(C),
#     stats = FALSE
#   )$logl}
#
# # CalcGLS <- function(y, X, vcov, logl = TRUE, stats = TRUE) {
#
# dim(y_l)
# dim(X_l)
#
# # Not executed since rho is parameter not value
# # Will run everything that doesn't involve rho to see what the final equation looks like
#
# vcov <-  C %*% CalcQ(rho, pm) %*% t(C)
#
# vcov_chk <-  C %*% CalcQ(0.5, pm) %*% t(C)

# x[0:3,0:2]
# array([[1, 5],
#        [2, 6],
#        [3, 7]])














# Step 2: Redo implementation with parameterized rho with sympy somehow (lol)


n_toep = len(X)


b = y_l
A = X_l
m = A.shape[0]
n = A.shape[1]
Q, R = linalg.qr(X_l)
R = R[~np.all(R == 0, axis=1)]
c_bB = Q.T.dot(b)
c_bB1 = c_bB[0:n]
c_bB2 = c_bB[n:m]


# rho = sym.symbols('rho')
# pm = np.array(toeplitz(np.arange(n_toep)),dtype=np.float64)
# sym_pm = sym.Matrix(pm)
# rho**pm

def func(rho):
    CalcQ = (1 / (1 - rho**2))*(rho**pm)
    vcov = (C.dot(CalcQ)).dot(C.T)
    W = vcov #
    B = np.linalg.cholesky(W) #
    C_bB = Q.T.dot(B) #
    C_bB1 = C_bB[0:n] #
    C_bB2 = C_bB[n:m] #
    C_bB2_T = C_bB2.T #
    ft_C_bB2 = np.flip(C_bB2_T[0:C_bB2_T.shape[0],0:C_bB2_T.shape[1]])
    PP, SS = linalg.qr(ft_C_bB2)
    SS = SS[~np.all(SS == 0, axis=1)]
    P = np.flip(PP[0:PP.shape[0], 0:PP.shape[1]])
    S = np.flip(SS[0:SS.shape[0], 0:SS.shape[1]]).T
    P1 = P[:, 0:n]
    P2 = P[:, n:m]
    u2 = solve_triangular(S,c_bB2)
    v = P2.dot(u2)
    v = v.reshape(len(v),1)
    x = solve_triangular(R, c_bB1 - C_bB1.dot(v))
    z_rss = u2.T.dot(u2)
    z_s_2 = z_rss/m
    z_logl = -m/2 - m*np.log(2*3.14)/2 - m*np.log(z_s_2)/2 - np.log(np.linalg.det(vcov))/2
    return -z_logl

func(0.5)

from scipy.optimize import minimize
from scipy.optimize import Bounds

x0 = [0.9]
bounds = Bounds([ -0.999],[ 0.999])
minimize(func,x0,bounds=bounds)