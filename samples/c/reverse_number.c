#include<stdio.h>
int main()
{
    int num,temp,sum=0,a;
    scanf("%d",&num);
    num=temp;
    while(num>0)
    {
        a=num%10;
        sum=sum*10+a;
        num/=10;
    }
    printf("%d",sum);
    return 0;
}
