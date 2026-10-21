ZDOTDIR=$A2A_USER_ZDOTDIR
# macOS /etc/zshrc ran while ZDOTDIR pointed here; history belongs to the user's directory.
[[ $HISTFILE == $A2A_TERMINAL_ZDOTDIR/.zsh_history ]] && HISTFILE=$ZDOTDIR/.zsh_history
[[ -f $ZDOTDIR/.zshrc ]] && source $ZDOTDIR/.zshrc
ZDOTDIR=$A2A_TERMINAL_ZDOTDIR
# The user's startup files may put their own bin directories first.
path=($A2A_TERMINAL_BIN ${path:#$A2A_TERMINAL_BIN})
