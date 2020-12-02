int main(int aa, int bb){

int a = 100;
int c = 200;
int b = a + c;

while( a < 0 ){
if(b > 0)continue;
b = b + c;
}

do{
c = c + 1;
a = a +1;
if(a == 1000)break;
}while(b > 100);

return 0;
}