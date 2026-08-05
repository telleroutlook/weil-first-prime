"""Unit tests for O1-B Schur assembly (no heavy integration calls)."""

from __future__ import annotations

from fractions import Fraction

import pytest

from src.assemble.o1b_gate import (
    build_gram,
    build_kinetic,
    build_R,
    build_R_eta,
    build_F,
    build_schur_matrix,
    _harmonic,
    ETA,
    L0,
)
from src.archimedean.interval import point


class TestHarmonic:
    def test_H1(self) -> None:
        assert _harmonic(1) == Fraction(1)

    def test_H4(self) -> None:
        assert _harmonic(4) == Fraction(25, 12)

    def test_H16(self) -> None:
        h = _harmonic(16)
        assert isinstance(h, Fraction)
        assert h > Fraction(3)  # H_16 ≈ 3.38


class TestGram:
    def test_even_diagonal(self) -> None:
        G = build_gram([0, 2, 4])
        assert G[0][0] == (Fraction(2, 1), Fraction(2, 1))   # 2/(2*0+1) = 2
        assert G[1][1] == (Fraction(2, 5), Fraction(2, 5))   # 2/(2*2+1) = 2/5
        assert G[2][2] == (Fraction(2, 9), Fraction(2, 9))   # 2/(2*4+1) = 2/9

    def test_off_diagonal_zero(self) -> None:
        G = build_gram([0, 2])
        assert G[0][1] == (Fraction(0), Fraction(0))
        assert G[1][0] == (Fraction(0), Fraction(0))


class TestKinetic:
    def test_T_n0(self) -> None:
        T = build_kinetic([0])
        # H_0 = 0; T[0][0] = 0 * 2/1 = 0
        assert T[0][0] == (Fraction(0), Fraction(0))

    def test_T_n2(self) -> None:
        T = build_kinetic([2])
        # H_2 = 1 + 1/2 = 3/2; G[0][0] = 2/5; T = 3/2 * 2/5 = 3/5
        assert T[0][0] == (Fraction(3, 5), Fraction(3, 5))


class TestSchurComplement:
    def test_R_zero_for_zero_M(self) -> None:
        N = 2
        M = [[point(Fraction(0))] * N for _ in range(N)]
        S = [[point(Fraction(1)), point(Fraction(0))],
             [point(Fraction(0)), point(Fraction(1))]]
        G = [[point(Fraction(2)), point(Fraction(0))],
             [point(Fraction(0)), point(Fraction(2))]]
        R = build_R(M, S, G)
        # R = S - 0 = S = I
        assert R[0][0] == (Fraction(1), Fraction(1))
        assert R[1][1] == (Fraction(1), Fraction(1))

    def test_R_eta_weights(self) -> None:
        N = 1
        R0 = [[point(Fraction(2))]]
        R2 = [[point(Fraction(1))]]
        # eta=1/2: c0=3/2, c2=3
        R_eta = build_R_eta(R0, R2)
        # (3/2)*2 + 3*1 = 3 + 3 = 6
        assert R_eta[0][0] == (Fraction(6), Fraction(6))


class TestFMatrix:
    def test_F_shifts_diagonal(self) -> None:
        N = 1
        T = [[point(Fraction(1))]]
        M0 = [[point(Fraction(Fraction(1, 2)))]]
        M2 = [[point(Fraction(0))]]
        G = [[point(Fraction(2))]]
        c_L = Fraction(1, 4)
        F = build_F(T, M0, M2, G, c_L)
        # F = 1 + 1/2 + 0 - (1/4 + L0) * 2
        expected = Fraction(1) + Fraction(1, 2) - (Fraction(1, 4) + L0) * 2
        assert F[0][0] == (expected, expected)


class TestSchurMatrix:
    def test_positive_result(self) -> None:
        N = 1
        b_L = Fraction(2)
        F = [[point(Fraction(3))]]
        R_eta = [[point(Fraction(1))]]
        C = build_schur_matrix(b_L, F, R_eta)
        # C = 2*3 - 1 = 5
        assert C[0][0] == (Fraction(5), Fraction(5))

    def test_negative_result(self) -> None:
        N = 1
        b_L = Fraction(1)
        F = [[point(Fraction(1))]]
        R_eta = [[point(Fraction(3))]]
        C = build_schur_matrix(b_L, F, R_eta)
        # C = 1*1 - 3 = -2
        assert C[0][0] == (Fraction(-2), Fraction(-2))
