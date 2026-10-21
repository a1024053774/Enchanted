# Enchanted terminal bootstrap (T-120). Each file sources the user's own file of the
# same name, then points ZDOTDIR back here so zsh reads the next file from this
# directory. The user's files are never changed.
ZDOTDIR=${A2A_USER_ZDOTDIR:-$HOME}
[[ -f $ZDOTDIR/.zshenv ]] && source $ZDOTDIR/.zshenv
A2A_USER_ZDOTDIR=$ZDOTDIR
ZDOTDIR=$A2A_TERMINAL_ZDOTDIR
