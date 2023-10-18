// This test file has not been compiled, it's just for "xgettext".

#include <stdio.h>
#include <libintl.h>

// In ".env", we specify a prefix as "_" so we can use it here.
#define _(STRING) gettext(STRING)
#define STR_MYSTRING _("These are a few words for you to look at, enjoy.")

int main(void)
{
    // Setup localization for platforms...
    // ...

    // Use gettext (or the prefix)
    printf("%s\n", STR_MYSTRING);
    return 0;
}