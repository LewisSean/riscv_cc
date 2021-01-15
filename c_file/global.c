int main(){
int ord[6] = { 0, 3, 2, 1, 4, 5 };
	int edge[6][6] = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
	int deg[6] = { 0, 0, 0, 0, 0, 0 };
	int que[6] = { 0, 0, 0, 0, 0, 0 };

	edge[ord[1]][ord[2]] = 1;
	edge[ord[1]][ord[3]] = 1;
	edge[ord[2]][ord[4]] = 1;
	edge[ord[3]][ord[4]] = 1;
	edge[ord[4]][ord[5]] = 1;
	deg[ord[1]] = 0;
	deg[ord[2]] = 1;
	deg[ord[3]] = 1;
	deg[ord[4]] = 2;
	deg[ord[5]] = 1;

	int n = 5;
	int l = 1;
	int r = 0;
	int cnt = 1;
	while (cnt <= n) {
		if (deg[cnt] == 0) {
			r += 1;
			que[r] = cnt;
		}
		cnt += 1;
	}
	cnt = 0;
	int res[6] = { 0,0,0,0,0,0 };
	while (l <= r) {
		int u = que[l];
		l += 1;
		cnt += 1;
		res[cnt] = u;
		int i = 1;
		while (i <= cnt) {
			if (edge[u][i] != 0) {
				deg[i] -= 1;
				if (deg[i] == 0) {
					r += 1;
					que[r] = i;
				}
			}
			i += 1;
		}
	}
    return 0;
}
