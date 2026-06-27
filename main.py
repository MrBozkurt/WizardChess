import chess
import stt
import os


pieces_map = {
        "pawn": chess.PAWN, "knight": chess.KNIGHT, "bishop": chess.BISHOP,
        "rook": chess.ROOK, "queen": chess.QUEEN, "king": chess.KING
    }

def parse_stt(parse, board):
    move = None

    #print(parse.piece_list)
    #print(parse.source)
    #print(parse.dest)

    # Source to destination
    if (parse.source and parse.dest):
        move = chess.Move.from_uci(parse.source + parse.dest)

    # Piece to destination
    elif (len(parse.piece_list) == 1 and parse.dest):
        piece = parse.piece_list[0]
        pieces = board.pieces(pieces_map[piece], board.turn)

        is_multiple = False

        for square in pieces:
            square_name = chess.square_name(square)
            temp_move = chess.Move.from_uci(square_name + parse.dest)
            if temp_move in board.legal_moves:
                if (not is_multiple):
                    move = temp_move
                    is_multiple = True
                else:
                    print("Multiple possibilites!")
                    return move

    # Piece to piece
    elif (len(parse.piece_list) == 2):
        source = parse.piece_list[0]
        sources = board.pieces(pieces_map[source], board.turn)

        taken = parse.piece_list[1]
        takens = board.pieces(pieces_map[taken], not board.turn)

        # One square given
        if (parse.dest):
            location = chess.parse_square(parse.dest)

            found_square = None
            found_target = None

            # Source square given
            for square in sources:
                if (square == location):
                    target_squares = board.attacks(square)
                    found_square = square

                    for target_square in target_squares:
                        target_piece = board.piece_at(target_square)
                        if (target_piece):
                            if (target_piece.piece_type == pieces_map[parse.piece_list[1]]):
                                if (found_target):
                                    print("Multiple possible targets!")
                                    move = None
                                    return move
                                else:
                                    found_target = target_square
                                    move = chess.Move.from_uci(chess.square_name(found_square) + chess.square_name(found_target))

            if (found_square or found_target):
                return move
            
            # Target square given
            for square in takens:
                if (square == location):
                    attacker_squares = board.attackers(board.turn, square)
                    found_target = square

                    print(".")

                    for attacker_square in attacker_squares:
                        attacker_piece = board.piece_at(attacker_square)
                        if (attacker_piece):
                            print("..")
                            if (attacker_piece.piece_type == pieces_map[parse.piece_list[0]]):
                                print("...")
                                if (found_square):
                                    print("Multiple possible attackers!")
                                    move = None
                                    return move
                                else:
                                    found_square = attacker_square
                                    move = chess.Move.from_uci(chess.square_name(found_square) + chess.square_name(found_target))

        # No square given
        else:
            for square in sources:
                target_squares = board.attacks(square)
                for target_square in target_squares:
                    target_piece = board.piece_at(target_square)
                    if (target_piece):
                        if (target_piece.piece_type == pieces_map[parse.piece_list[1]]):
                            if (move):
                                print("Multiple possible targets!")
                                move = None
                                return move
                            else:
                                move = chess.Move.from_uci(chess.square_name(square) + chess.square_name(target_square))

    print(move)
    return move

def piece_to_code(piece):
    if (piece):
        if (piece == "knight"):
            piece = "n"
        else:
            piece = piece[0]

def main():
    stt.setup()
    os.system('cls' if os.name=='nt' else 'clear')
    board = chess.Board()

    print(board)
    print("WHITE" if board.turn else "black")

    while True:
        text = input()
        move = None

        if (text == "a"):
            sound = stt.parseSound()
            move = parse_stt(sound, board)
        elif (text=="z" or text=="b"):
            break
        elif (text == "reverse"):
            board.pop()
        else:
            parse_text = stt.parse(text)
            move = parse_stt(parse_text, board)

        if (move):
            if move in board.legal_moves:
                board.push(move)
            else:
                print("Not a legal move!")
        
        os.system('cls' if os.name=='nt' else 'clear')
        print(board)
        print("WHITE" if board.turn else "black")
                

if __name__ == "__main__":
    main()