int main(){
int a = 100;
int c = 200;
int b = a + c;
while(b < 4) b++;
do{
c = c + 1;
a = a +1;
}while(b > 100);
return b;
}