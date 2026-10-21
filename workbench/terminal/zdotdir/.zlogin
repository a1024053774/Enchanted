ZDOTDIR=$A2A_USER_ZDOTDIR
[[ -f $ZDOTDIR/.zlogin ]] && source $ZDOTDIR/.zlogin
path=($A2A_TERMINAL_BIN ${path:#$A2A_TERMINAL_BIN})
# Last startup file: leave ZDOTDIR as the user's environment or startup files set it.
if [[ -n ${A2A_USER_ZDOTDIR_SET-} || $A2A_USER_ZDOTDIR != $HOME ]]; then ZDOTDIR=$A2A_USER_ZDOTDIR; else unset ZDOTDIR; fi
unset A2A_USER_ZDOTDIR A2A_USER_ZDOTDIR_SET A2A_TERMINAL_ZDOTDIR
