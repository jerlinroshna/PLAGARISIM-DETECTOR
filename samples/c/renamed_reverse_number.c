#include<stdio.h>
int main()
{
    int value,holder,reversed=0,digit;
    scanf("%d",&value);
    value=holder;
    while(value>0)
    {
        digit=value%10;
        reversed=reversed*10+digit;
        value/=10;
    }
    printf("%d",reversed);
    return 0;
}
