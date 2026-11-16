# An idea's checks

Knight judges each hit against the idea's checks: numbered lines, each a fact Knight can settle from the board after the move and the moves around it. Together they hold for a textbook example and fail for the near misses a coach wouldn't put in a lesson. `judge.py` sends them with each hit, and Knight goes through them one by one before its verdict.

Copy an idea's checks below, as written, into a file of their own, such as `checks/back-rank-mate.txt`, with no heading. Use the person's words for `--idea`.

## Back rank mate

```text
1. The move gives checkmate.
2. The mated king stands on its own first rank: rank 1 for White, rank 8 for Black.
3. The piece that gives mate is a rook or a queen, and the board's line about the move says it attacks the king along that same rank.
4. The board's line about the move says the mating piece isn't next to the enemy king.
5. The board's line about the mated king names at least one of its own pieces in front of it, usually a pawn, so the king is shut in on its first rank.
6. It isn't a bare ending: each side has more than a king and the mating piece.
```

## Knight fork

```text
1. The piece that moves is a knight.
2. The board's line about the move lists two or more enemy pieces the knight attacks, not counting pawns.
3. It wins something: in the moves that follow, the knight takes one of those pieces, or the other side gives up material to save its king or queen.
```

## Discovered attack

```text
1. The board's line about the move says moving it uncovered a rook, bishop or queen, which now attacks an enemy piece.
2. It wins something: in the moves that follow, the side that moved takes a piece, and the other side doesn't take back as much.
```

## Another idea

Write its checks in the same shape before the first hit, and give them to the person in your answer, as "I counted a hit as a smothered mate when: …", so they can correct them:

- **One fact a line,** in the board's own words: the move, the piece that moves, where the kings stand, the squares around a king, what the moved piece attacks, what the next moves take. Knight reads those from the board's lines.
- **Name the near misses a coach would turn down,** and add a check that fails for each, as checks 4 and 6 of a back rank mate do for a queen mating next to the king and for a bare ending.
- **What the moves must win, if anything:** say so in the moves that follow, not as an evaluation.
- Three to six checks. Leave out anything Knight can't read from the board and the moves, such as a player's plan.

Never judge a hit yourself, against the checks or otherwise. Knight goes through them.
